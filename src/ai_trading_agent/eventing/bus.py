from __future__ import annotations

from ai_trading_agent.contracts.agent import AgentEvent


class EventBusError(ValueError):
    pass


class EventBus:
    """Append-only, in-memory event bus with deterministic sequence assignment."""

    def __init__(self) -> None:
        self._events: tuple[AgentEvent, ...] = ()
        self._by_id: dict[str, AgentEvent] = {}
        self._sequence: dict[str, int] = {}

    def publish(self, event: AgentEvent) -> AgentEvent:
        key = str(event.event_id)
        existing = self._by_id.get(key)
        if existing is not None:
            if existing.model_dump() != event.model_dump():
                raise EventBusError("event_id reused with different payload")
            return existing

        if event.causation_id is not None and str(event.causation_id) not in self._by_id:
            raise EventBusError("causation_id must reference an existing event")

        seq = len(self._events) + 1
        self._events = self._events + (event,)
        self._by_id[key] = event
        self._sequence[key] = seq
        return event

    def get(self, event_id: str) -> AgentEvent:
        try:
            return self._by_id[event_id]
        except KeyError as exc:
            raise EventBusError("event not found") from exc

    def sequence(self, event_id: str) -> int:
        try:
            return self._sequence[event_id]
        except KeyError as exc:
            raise EventBusError("event not found") from exc

    def stream(
        self,
        *,
        correlation_id=None,
        task_id=None,
        until_sequence: int | None = None,
    ) -> tuple[AgentEvent, ...]:
        if correlation_id is None and task_id is None:
            raise EventBusError("stream requires correlation_id or task_id")
        if until_sequence is not None and until_sequence < 0:
            raise EventBusError("until_sequence must be non-negative")

        out = []
        for event in self._events:
            seq = self._sequence[str(event.event_id)]
            if until_sequence is not None and seq > until_sequence:
                break
            if correlation_id is not None and event.correlation_id != correlation_id:
                continue
            if task_id is not None and event.task_id != task_id:
                continue
            out.append(event)
        return tuple(out)

    @property
    def events(self) -> tuple[AgentEvent, ...]:
        return self._events
