from __future__ import annotations
from hashlib import sha256
from uuid import UUID
from ai_trading_agent.contracts.agent import AgentEvent, AgentPermission, AgentPermissionSet, AgentResult, AgentTask, AgentTaskStatus
from ai_trading_agent.core.models import Approval, OrderFilled, TradeIntent

class AgentTeamBoundaryError(PermissionError):
    pass

class AgentTeamBoundary:
    """Fail-closed adapter between Agent Teams contracts and Frozen Core.

    Agent Teams can schedule, research, emit proposals/events and read decisions.
    They cannot manufacture approval, bypass RiskGate, or submit an order directly.
    """
    _TRANSITIONS = {
        AgentTaskStatus.CREATED: {AgentTaskStatus.ASSIGNED, AgentTaskStatus.REJECTED, AgentTaskStatus.BLOCKED},
        AgentTaskStatus.ASSIGNED: {AgentTaskStatus.RUNNING, AgentTaskStatus.REJECTED, AgentTaskStatus.BLOCKED},
        AgentTaskStatus.RUNNING: {AgentTaskStatus.WAITING, AgentTaskStatus.VALIDATING, AgentTaskStatus.COMPLETED, AgentTaskStatus.FAILED, AgentTaskStatus.BLOCKED},
        AgentTaskStatus.WAITING: {AgentTaskStatus.RUNNING, AgentTaskStatus.BLOCKED, AgentTaskStatus.FAILED},
        AgentTaskStatus.VALIDATING: {AgentTaskStatus.COMPLETED, AgentTaskStatus.FAILED, AgentTaskStatus.REJECTED},
        AgentTaskStatus.COMPLETED: set(), AgentTaskStatus.FAILED: set(), AgentTaskStatus.REJECTED: set(), AgentTaskStatus.BLOCKED: set(),
    }
    def __init__(self):
        self._idempotency: dict[str, AgentEvent] = {}

    def transition(self, task: AgentTask, status: AgentTaskStatus) -> AgentTask:
        if status not in self._TRANSITIONS[task.status]:
            raise AgentTeamBoundaryError(f"invalid task transition: {task.status}->{status}")
        return task.model_copy(update={"status": status})

    def require(self, permissions: AgentPermissionSet, permission: AgentPermission) -> None:
        if not permissions.allows(permission):
            raise AgentTeamBoundaryError(f"permission denied: {permission.value}")

    def validate_event(self, event: AgentEvent, task: AgentTask) -> None:
        if event.task_id != task.task_id or event.correlation_id != task.correlation_id:
            raise AgentTeamBoundaryError("event correlation/task mismatch")
        if event.causation_id == event.event_id:
            raise AgentTeamBoundaryError("event cannot cause itself")

    def publish_idempotent(self, event: AgentEvent) -> AgentEvent:
        existing = self._idempotency.get(str(event.event_id))
        if existing is not None:
            if existing.model_dump() != event.model_dump():
                raise AgentTeamBoundaryError("event id reused with different payload")
            return existing
        self._idempotency[str(event.event_id)] = event
        return event

    @staticmethod
    def validate_artifact_refs(refs: list[str]) -> None:
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise AgentTeamBoundaryError("artifact reference must be non-empty")

    @staticmethod
    def validate_result(result: AgentResult, task: AgentTask) -> None:
        if result.task_id != task.task_id or result.correlation_id != task.correlation_id:
            raise AgentTeamBoundaryError("result correlation/task mismatch")
        AgentTeamBoundary.validate_artifact_refs(result.artifact_refs)
        if result.status.value == "SUCCESS" and not result.validation_passed:
            raise AgentTeamBoundaryError("SUCCESS result must pass validation")

    @staticmethod
    def reject_bypass(action: str) -> None:
        forbidden = {"RISK_GATE_BYPASS", "APPROVAL_BYPASS", "DIRECT_EXECUTION", "EXECUTE", "LLM_EXECUTE"}
        if action in forbidden:
            raise AgentTeamBoundaryError(f"forbidden agent action: {action}")

    @staticmethod
    def execution_boundary(intent: TradeIntent, approval: Approval, fill: OrderFilled | None) -> OrderFilled:
        if fill is None:
            raise AgentTeamBoundaryError("ExecutionPort must return OrderFilled")
        if not approval.approved or not approval.risk_gate_allowed:
            raise AgentTeamBoundaryError("execution requires RiskGate approval")
        if fill.intent_id != intent.intent_id or fill.fill_size != intent.contracts:
            raise AgentTeamBoundaryError("OrderFilled provenance mismatch")
        return fill

    @staticmethod
    def deterministic_replay(events: list[AgentEvent]) -> str:
        canonical = "|".join(str(e.model_dump_json()) for e in events)
        return sha256(canonical.encode()).hexdigest()
