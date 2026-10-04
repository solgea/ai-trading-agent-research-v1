# AT-1 — Agent Teams ↔ Frozen Core Integration

Status: IMPLEMENTED — pending CI freeze gate.

## Boundary
Agent Teams are contract-driven orchestration/research actors. Frozen Core remains the sole authority for TradeIntent → RiskGate → Approval → ExecutionPort → OrderFilled.

## Required invariants
- AgentTask lifecycle is explicit and terminal states cannot transition.
- Roles and permissions are enum-validated; there is no generic EXECUTE permission.
- Events carry task/correlation/causation identity and are idempotent by event id.
- Artifact references are non-empty and results must match task/correlation provenance.
- Agents cannot bypass RiskGate or Approval.
- Agents and LLM cannot submit orders directly.
- Execution is only observed through ExecutionPort and represented by OrderFilled.
- Replay of the same event sequence is deterministic.
- Unknown/forbidden bypass actions fail closed.

## Gate
AT1-001 through AT1-018 must pass, followed by GitHub Actions PASS. Only then is AT-1 FROZEN.
