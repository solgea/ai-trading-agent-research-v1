from __future__ import annotations
from abc import ABC, abstractmethod
from decimal import Decimal
from .models import Approval, OrderFilled, TradeIntent

class ExecutionPort(ABC):
    @abstractmethod
    def submit(self, intent: TradeIntent, approval: Approval) -> OrderFilled: ...

class MockExecutionPort(ExecutionPort):
    """Deterministic execution for research/demo tests; no network access."""
    def submit(self, intent: TradeIntent, approval: Approval) -> OrderFilled:
        if not approval.approved or not approval.risk_gate_allowed:
            raise PermissionError("execution requires approved RiskGate decision")
        return OrderFilled(
            intent_id=intent.intent_id,
            order_id=f"mock-{intent.intent_id}",
            fill_price=intent.entry,
            fill_size=intent.contracts,
            fees=Decimal("0"),
            fee_currency="USDT",
            maker=False,
            execution_mode="MOCK",
        )
