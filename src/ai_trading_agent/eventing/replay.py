from __future__ import annotations

from hashlib import sha256
import json
from ai_trading_agent.contracts.agent import AgentEvent


class ReplayError(ValueError):
    pass


class Replay:
    """Deterministic replay over an explicitly bounded event stream."""

    @staticmethod
    def _canonical(events: tuple[AgentEvent, ...]) -> bytes:
        payload = [
            e.model_dump(mode="json")
            for e in events
        ]
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    def replay(
        self,
        events: list[AgentEvent] | tuple[AgentEvent, ...],
        *,
        until_sequence: int | None = None,
    ) -> tuple[AgentEvent, ...]:
        if until_sequence is not None and until_sequence < 0:
            raise ReplayError("until_sequence must be non-negative")
        if not events:
            return ()
        # Sequence is the supplied stream order; replay never invents future events.
        selected = tuple(events[:until_sequence]) if until_sequence is not None else tuple(events)
        if any(not isinstance(e, AgentEvent) for e in selected):
            raise ReplayError("invalid event stream")
        seen: set[str] = set()
        for event in selected:
            key = str(event.event_id)
            if key in seen:
                raise ReplayError("duplicate event in replay stream")
            seen.add(key)
        return selected

    def digest(self, events: list[AgentEvent] | tuple[AgentEvent, ...]) -> str:
        return sha256(self._canonical(tuple(events))).hexdigest()
