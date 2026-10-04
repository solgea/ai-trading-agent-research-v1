from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from ai_trading_agent.contracts.agent import AgentEvent


class ResearchMemoryError(ValueError):
    pass


class MemoryMode(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"


class MemoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    memory_id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    created_at: datetime
    mode: MemoryMode = MemoryMode.RESEARCH_ONLY
    content: str = Field(min_length=1)
    artifact_ref: str = Field(min_length=1)
    provenance_ref: str = Field(min_length=1)


class ResearchMemory:
    """Immutable research memory. It has no approval or execution authority."""

    def __init__(self) -> None:
        self._entries: tuple[MemoryEntry, ...] = ()
        self._by_id: dict[UUID, MemoryEntry] = {}

    def write(self, *, event: AgentEvent, content: str, artifact_ref: str, provenance_ref: str) -> MemoryEntry:
        if not content.strip() or not artifact_ref.strip() or not provenance_ref.strip():
            raise ResearchMemoryError("memory content, artifact_ref and provenance_ref are required")
        entry = MemoryEntry(
            event_id=event.event_id,
            created_at=datetime.now(timezone.utc),
            content=content,
            artifact_ref=artifact_ref,
            provenance_ref=provenance_ref,
        )
        self._entries = self._entries + (entry,)
        self._by_id[entry.memory_id] = entry
        return entry

    def get(self, memory_id: UUID) -> MemoryEntry:
        try:
            return self._by_id[memory_id]
        except KeyError as exc:
            raise ResearchMemoryError("memory entry not found") from exc

    @property
    def entries(self) -> tuple[MemoryEntry, ...]:
        return self._entries

    def reject_authority_action(self, action: str) -> None:
        raise ResearchMemoryError(f"research memory cannot authorize action: {action}")
