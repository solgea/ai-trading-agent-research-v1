from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from .models import *
from .risk import RiskGate
from .execution import ExecutionPort

class FrozenCoreOrchestrator:
    """Canonical pipeline; LLM and agents cannot bypass risk/approval."""
    def __init__(self, risk_gate: RiskGate, execution_port: ExecutionPort):
        self.risk_gate = risk_gate
        self.execution_port = execution_port
    def propose(self, snapshot: MarketSnapshot, smc: SMCResult, signal: SignalCandidate,
                entry: Decimal, stop_loss: Decimal, take_profit: Decimal,
                contracts: Decimal, risk_pct: Decimal, max_loss: Decimal, notional: Decimal) -> TradeIntent:
        if smc.snapshot_id != snapshot.snapshot_id or signal.snapshot_id != snapshot.snapshot_id:
            raise ValueError("provenance mismatch")
        return TradeIntent(signal_id=signal.signal_id, snapshot_id=snapshot.snapshot_id,
            side=signal.side, entry=entry, stop_loss=stop_loss, take_profit=take_profit,
            contracts=contracts)
    def approve(self, intent: TradeIntent, proposal: RiskProposal) -> Approval:
        decision = self.risk_gate.evaluate(intent, proposal)
        return Approval(intent_id=intent.intent_id, approved=decision.allowed,
                        risk_gate_allowed=decision.allowed)
    def execute(self, intent: TradeIntent, approval: Approval) -> OrderFilled:
        return self.execution_port.submit(intent, approval)
