from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from ai_trading_agent.contracts.agent import *
from ai_trading_agent.core import *
from ai_trading_agent.integration import AgentTeamBoundary, AgentTeamBoundaryError


def task_and_boundary():
    tid, cid = uuid4(), uuid4()
    task = AgentTask(task_id=tid, team_id="team-1", agent_id="signal-1", role=AgentRole.SIGNAL,
        task_type="SIGNAL_RESEARCH", correlation_id=cid, idempotency_key="idem-1", expected_result_type="SignalCandidate",
        created_at=datetime.now(timezone.utc), required_permissions=[AgentPermission.SIGNAL_CREATE])
    return task, AgentTeamBoundary()


def event_for(task, event_id=None, causation_id=None):
    return AgentEvent(event_id=event_id or uuid4(), event_type="SignalCreated", schema_version="1.0",
        producer_agent_id=task.agent_id, producer_role=task.role, correlation_id=task.correlation_id,
        causation_id=causation_id, task_id=task.task_id, timestamp=datetime.now(timezone.utc),
        artifact_refs=["sha256:" + "a"*64], payload_hash="b"*64, payload_type="SignalCandidate")


def core_chain():
    sid=uuid4(); snap=MarketSnapshot(snapshot_id=sid,instrument="BTC-USDT-SWAP",timeframe="15m",observed_at=datetime.now(timezone.utc),close=Decimal("60000"),sequence=1,data_hash="a"*64)
    smc=SMCResult(snapshot_id=sid,structure="HH_HL",liquidity_swept=True,mss_confirmed=True,bos_confirmed=True,ob_confirmed=True,fvg_confirmed=True,provenance_snapshot_id=sid)
    sig=SignalCandidate(snapshot_id=sid,side="LONG",confidence=Decimal("0.85"),rationale="AT-1")
    orch=FrozenCoreOrchestrator(RiskGate(),MockExecutionPort())
    intent=orch.propose(snap,smc,sig,Decimal("60000"),Decimal("59000"),Decimal("62000"),Decimal("1"),Decimal("0.005"),Decimal("50"),Decimal("60000"))
    proposal=RiskProposal(intent_id=intent.intent_id,risk_pct=Decimal("0.005"),max_loss=Decimal("50"),notional=Decimal("60000"))
    approval=orch.approve(intent,proposal); fill=orch.execute(intent,approval)
    return intent, approval, fill


def test_at1_001_task_lifecycle():
    task,b=task_and_boundary(); task=b.transition(task,AgentTaskStatus.ASSIGNED); task=b.transition(task,AgentTaskStatus.RUNNING); task=b.transition(task,AgentTaskStatus.VALIDATING); task=b.transition(task,AgentTaskStatus.COMPLETED); assert task.status is AgentTaskStatus.COMPLETED

def test_at1_002_role_validation():
    task,_=task_and_boundary(); assert task.role is AgentRole.SIGNAL
    with pytest.raises(Exception): AgentTask.model_validate({**task.model_dump(mode="json"),"role":"NOT_A_ROLE"})

def test_at1_003_permission_allow():
    _,b=task_and_boundary(); b.require(AgentPermissionSet(permissions=[AgentPermission.SIGNAL_CREATE]),AgentPermission.SIGNAL_CREATE)

def test_at1_004_permission_deny():
    _,b=task_and_boundary()
    with pytest.raises(AgentTeamBoundaryError): b.require(AgentPermissionSet(),AgentPermission.SIGNAL_CREATE)

def test_at1_005_event_correlation():
    task,b=task_and_boundary(); b.validate_event(event_for(task),task)
    bad=event_for(task); bad=bad.model_copy(update={"correlation_id":uuid4()})
    with pytest.raises(AgentTeamBoundaryError): b.validate_event(bad,task)

def test_at1_006_event_causation():
    task,b=task_and_boundary(); first=event_for(task); second=event_for(task,causation_id=first.event_id); b.validate_event(second,task); assert second.causation_id==first.event_id

def test_at1_007_idempotency():
    task,b=task_and_boundary(); e=event_for(task); assert b.publish_idempotent(e)==b.publish_idempotent(e)
    with pytest.raises(AgentTeamBoundaryError): b.publish_idempotent(e.model_copy(update={"payload_hash":"c"*64}))

def test_at1_008_artifact_reference_integrity():
    AgentTeamBoundary.validate_artifact_refs(["sha256:"+"a"*64])
    with pytest.raises(AgentTeamBoundaryError): AgentTeamBoundary.validate_artifact_refs([""])

def test_at1_009_agent_result_validation():
    task,b=task_and_boundary(); r=AgentResult(result_id=uuid4(),task_id=task.task_id,agent_id=task.agent_id,role=task.role,status=AgentResultStatus.SUCCESS,result_type="SignalCandidate",artifact_refs=["sha256:"+"a"*64],validation_passed=True,created_at=datetime.now(timezone.utc),correlation_id=task.correlation_id); b.validate_result(r,task)

def test_at1_010_risk_gate_bypass_rejection():
    with pytest.raises(AgentTeamBoundaryError): AgentTeamBoundary.reject_bypass("RISK_GATE_BYPASS")

def test_at1_011_approval_bypass_rejection():
    with pytest.raises(AgentTeamBoundaryError): AgentTeamBoundary.reject_bypass("APPROVAL_BYPASS")

def test_at1_012_direct_execution_rejection():
    with pytest.raises(AgentTeamBoundaryError): AgentTeamBoundary.reject_bypass("DIRECT_EXECUTION")

def test_at1_013_llm_execution_rejection():
    with pytest.raises(AgentTeamBoundaryError): AgentTeamBoundary.reject_bypass("LLM_EXECUTE")

def test_at1_014_execute_permission_absence():
    assert not hasattr(AgentPermission,"EXECUTE")
    assert "EXECUTE" not in [p.value for p in AgentPermission]

def test_at1_015_execution_port_boundary():
    intent,approval,fill=core_chain(); checked=AgentTeamBoundary.execution_boundary(intent,approval,fill); assert checked.execution_mode=="MOCK"
    with pytest.raises(AgentTeamBoundaryError): AgentTeamBoundary.execution_boundary(intent,approval, None)

def test_at1_016_order_filled_provenance():
    intent,approval,fill=core_chain(); assert fill.intent_id==intent.intent_id; assert fill.fill_size==intent.contracts
    with pytest.raises(AgentTeamBoundaryError): AgentTeamBoundary.execution_boundary(intent,approval,fill.model_copy(update={"intent_id":uuid4()}))

def test_at1_017_replay_determinism():
    task,b=task_and_boundary(); e1=event_for(task); e2=event_for(task,causation_id=e1.event_id); assert b.deterministic_replay([e1,e2])==b.deterministic_replay([e1,e2])

def test_at1_018_fail_closed_behavior():
    task,b=task_and_boundary()
    with pytest.raises(AgentTeamBoundaryError): b.reject_bypass("UNKNOWN_BYPASS")
