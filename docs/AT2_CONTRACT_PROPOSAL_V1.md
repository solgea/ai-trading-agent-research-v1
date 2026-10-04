# AT-2 Contract Proposal v1 — Event Bus, Replay & Research Memory

Status: **PROPOSAL — OPEN FOR IMPLEMENTATION**

Base: AT-1 merged commit `f1e21863d35958ec7f1387fbbed1236ea7185bbf`

## 1. Scope

AT-2 establishes the deterministic event infrastructure between Agent Teams and Frozen Core:

`AgentEvent -> EventBus -> Replay -> ResearchMemory`

This phase does **not** add live execution, exchange connectivity, LLM authority, or an EXECUTE capability.

## 2. Locked invariants

1. **Append-only events** — published events are immutable.
2. **Idempotency** — the same event_id + identical payload is accepted once; reuse with a different payload is rejected.
3. **Correlation integrity** — task_id and correlation_id must remain consistent.
4. **Causation integrity** — causation_id cannot self-reference and must reference an existing event when supplied.
5. **Deterministic ordering** — replay uses explicit sequence/order, never wall-clock sorting alone.
6. **Deterministic replay** — identical event streams produce the identical replay digest.
7. **Research-only memory** — memory defaults to `RESEARCH_ONLY`; memory cannot authorize or submit orders.
8. **No execution bypass** — EventBus, Replay, and Memory cannot call ExecutionPort directly.
9. **Fail-closed validation** — malformed events, broken references, duplicate-conflict events, and invalid memory writes are rejected.
10. **No look-ahead** — replay/memory APIs may only consume events available at or before the replay boundary.

## 3. Canonical contracts

### EventBus

Required operations:
- `publish(event)`
- `get(event_id)`
- `stream(correlation_id/task_id, until_sequence)`

The bus must preserve the canonical event payload and reject mutation.

### Replay

Required operations:
- `replay(events, until_sequence=None)`
- `digest(events)`

Replay output must be deterministic and independently verifiable.

### ResearchMemory

Memory entry must contain:
- `memory_id`
- `event_id`
- `created_at`
- `mode=RESEARCH_ONLY`
- immutable content/artifact reference
- provenance reference

Writes without provenance are rejected.

## 4. Forbidden behavior

AT-2 MUST reject:
- `EXECUTE`
- direct ExecutionPort invocation
- approval creation
- RiskGate bypass
- mutation of historical events
- memory writes presented as authoritative trading decisions
- replay beyond the supplied temporal boundary
- duplicate event_id with altered payload

## 5. Test gate

AT2-001 Event append
AT2-002 Event immutability
AT2-003 Idempotent duplicate
AT2-004 Conflicting duplicate rejection
AT2-005 Correlation integrity
AT2-006 Causation integrity
AT2-007 Deterministic ordering
AT2-008 Deterministic replay digest
AT2-009 Replay boundary / no look-ahead
AT2-010 Research-only memory write
AT2-011 Memory provenance
AT2-012 Invalid memory write rejection
AT2-013 Execution bypass rejection
AT2-014 Approval bypass rejection
AT2-015 RiskGate bypass rejection
AT2-016 Historical event mutation rejection
AT2-017 Cross-task event rejection
AT2-018 Full event-stream replay consistency

## 6. Freeze gate

AT-2 may be marked **FROZEN** only when:

- all AT2-001..AT2-018 pass;
- contract/schema parity tests pass;
- CI passes on the AT-2 PR;
- no execution path is introduced;
- replay determinism is demonstrated;
- ResearchMemory remains `RESEARCH_ONLY`.

Until then: **NOT FROZEN**.
