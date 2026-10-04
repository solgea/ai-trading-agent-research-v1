# AT-2 Implementation V1

Status: IMPLEMENTED — pending CI gate.

Scope: append-only EventBus, deterministic Replay, and immutable RESEARCH_ONLY ResearchMemory.

Canonical flow:
AgentEvent -> EventBus -> Replay -> ResearchMemory

Safety invariants:
- event history is append-only and duplicate IDs are idempotent only when identical;
- conflicting event IDs fail closed;
- causation must reference an existing event;
- stream order is explicit insertion sequence;
- replay is bounded by the supplied sequence boundary and never invents future events;
- memory entries are immutable and default to RESEARCH_ONLY;
- memory exposes no approval, RiskGate, or ExecutionPort capability;
- malformed writes fail closed.

Gate: AT2-001 through AT2-018 plus existing Agent/Core contract suites must pass in CI.
No live exchange or execution path is introduced by AT-2.
