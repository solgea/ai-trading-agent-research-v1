from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from .models import RiskProposal, TradeIntent, RiskGateDecision

class RiskGate:
    """Fail-closed, deterministic risk boundary. Never submits orders."""
    def __init__(self, max_risk_pct: Decimal = Decimal("0.01")):
        self.max_risk_pct = max_risk_pct
    def evaluate(self, intent: TradeIntent, proposal: RiskProposal) -> RiskGateDecision:
        try:
            valid = (
                proposal.intent_id == intent.intent_id and
                proposal.risk_pct <= self.max_risk_pct and
                proposal.max_loss > 0 and proposal.notional > 0
            )
        except (InvalidOperation, TypeError, ValueError):
            valid = False
        return RiskGateDecision(
            intent_id=intent.intent_id,
            allowed=bool(valid),
            reason="RISK_OK" if valid else "RISK_REJECTED",
            checked_at=datetime.now(timezone.utc),
        )
