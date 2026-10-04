# Frozen Core V1

Status: **IMPLEMENTED — FROZEN CORE BASELINE PENDING CI**

The original Frozen Core source was not recoverable from the connected repository. This implementation establishes a new canonical baseline without importing behavior from unrelated OKX runtime projects.

## Invariants
- No look-ahead: every SMC/signal artifact carries the exact MarketSnapshot provenance.
- Immutable domain objects: Pydantic models are frozen and reject unknown fields.
- LLM advisory-only: LLM cannot approve, submit, or execute.
- Risk independent: RiskGate is deterministic, Decimal-based, fail-closed, and has no execution dependency.
- Approval required: ExecutionPort accepts only an approved RiskGate decision.
- OrderFilled is fill reality and records price, size, fees, currency, maker flag, and execution mode.
- Demo first: MockExecutionPort is the only execution implementation in this baseline; no network client is enabled.

## Canonical flow
Agent → SMCResult → SignalCandidate → TradeIntent → RiskProposal → RiskGate → Approval → ExecutionPort → OrderFilled

## Explicit non-goals
This baseline does not enable live trading, does not contain OKX credentials, and does not allow an LLM or Agent Team to bypass RiskGate or Approval.
