from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError

from ai_trading_agent.contracts.agent import AgentEvent, AgentRole
from ai_trading_agent.eventing import EventBus, EventBusError, Replay, ResearchMemory, ResearchMemoryError, MemoryMode


def event(*, correlation_id=None, task_id=None, causation_id=None, event_id=None, n="0"):
    cid = correlation_id or uuid4()
    tid = task_id or uuid4()
    return AgentEvent(
        event_id=event_id or uuid4(),
        event_type="TEST.EVENT",
        schema_version="1.0",
        producer_agent_id="agent-test",
        producer_role=AgentRole.RESEARCH,
        correlation_id=cid,
        causation_id=causation_id,
        task_id=tid,
        timestamp=datetime(2026, 10, 5, 12, 0, int(n), tzinfo=timezone.utc),
        artifact_refs=["artifact://test"],
        payload_hash=(n.zfill(64)),
        payload_type="TestPayload",
    )


def test_AT2_001_event_append():
    bus = EventBus()
    e = event()
    assert bus.publish(e) == e
    assert bus.events == (e,)


def test_AT2_002_event_immutability():
    bus = EventBus()
    e = event()
    bus.publish(e)
    with pytest.raises(ValidationError, match="Instance is frozen"):
        e.event_type = "MUTATED"
    assert bus.get(str(e.event_id)).event_type == "TEST.EVENT"


def test_AT2_003_idempotent_duplicate():
    bus = EventBus()
    e = event()
    assert bus.publish(e) == bus.publish(e)
    assert len(bus.events) == 1


def test_AT2_004_conflicting_duplicate_rejected():
    bus = EventBus()
    eid = uuid4()
    bus.publish(event(event_id=eid, n="1"))
    with pytest.raises(EventBusError):
        bus.publish(event(event_id=eid, n="2"))


def test_AT2_005_correlation_integrity():
    bus = EventBus()
    e = event()
    bus.publish(e)
    other = event(correlation_id=uuid4())
    assert bus.stream(correlation_id=e.correlation_id) == (e,)
    assert other not in bus.stream(correlation_id=e.correlation_id)


def test_AT2_006_causation_integrity():
    bus = EventBus()
    parent = event()
    bus.publish(parent)
    child = event(correlation_id=parent.correlation_id, task_id=parent.task_id, causation_id=parent.event_id)
    assert bus.publish(child) == child
    with pytest.raises(EventBusError):
        bus.publish(event(causation_id=uuid4()))


def test_AT2_007_deterministic_ordering():
    bus = EventBus()
    a, b = event(n="1"), event(n="2")
    bus.publish(a); bus.publish(b)
    assert bus.events == (a, b)
    assert bus.sequence(str(a.event_id)) == 1
    assert bus.sequence(str(b.event_id)) == 2


def test_AT2_008_deterministic_replay_digest():
    a, b = event(n="1"), event(n="2")
    replay = Replay()
    assert replay.digest([a, b]) == replay.digest([a, b])


def test_AT2_009_replay_boundary_no_lookahead():
    events = [event(n="1"), event(n="2"), event(n="3")]
    assert Replay().replay(events, until_sequence=2) == tuple(events[:2])


def test_AT2_010_research_only_memory_write():
    e = event()
    memory = ResearchMemory()
    entry = memory.write(event=e, content="research note", artifact_ref="artifact://1", provenance_ref=str(e.event_id))
    assert entry.mode is MemoryMode.RESEARCH_ONLY


def test_AT2_011_memory_provenance():
    memory = ResearchMemory()
    e = event()
    entry = memory.write(event=e, content="note", artifact_ref="artifact://1", provenance_ref=str(e.event_id))
    assert entry.event_id == e.event_id
    assert entry.provenance_ref == str(e.event_id)


def test_AT2_012_invalid_memory_write_rejected():
    with pytest.raises(ResearchMemoryError):
        ResearchMemory().write(event=event(), content="", artifact_ref="a", provenance_ref="p")


def test_AT2_013_execution_bypass_rejection():
    with pytest.raises(ResearchMemoryError):
        ResearchMemory().reject_authority_action("EXECUTE")


def test_AT2_014_approval_bypass_rejection():
    with pytest.raises(ResearchMemoryError):
        ResearchMemory().reject_authority_action("APPROVE")


def test_AT2_015_risk_gate_bypass_rejection():
    with pytest.raises(ResearchMemoryError):
        ResearchMemory().reject_authority_action("RISK_GATE_BYPASS")


def test_AT2_016_historical_event_mutation_rejection():
    bus = EventBus()
    e = event()
    bus.publish(e)
    with pytest.raises(EventBusError):
        bus.publish(e.model_copy(update={"payload_hash": "f" * 64}))


def test_AT2_017_cross_task_event_rejection():
    bus = EventBus()
    e = event()
    bus.publish(e)
    assert bus.stream(task_id=uuid4()) == ()


def test_AT2_018_full_event_stream_replay_consistency():
    bus = EventBus()
    root = event(n="1")
    child = event(correlation_id=root.correlation_id, task_id=root.task_id, causation_id=root.event_id, n="2")
    bus.publish(root); bus.publish(child)
    stream = bus.stream(correlation_id=root.correlation_id)
    replay = Replay()
    assert replay.replay(stream) == stream
    assert replay.digest(list(stream)) == replay.digest(list(replay.replay(stream)))
