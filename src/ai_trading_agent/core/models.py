from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, model_validator

class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

class SignalSide(str, Enum):
    LONG="LONG"
    SHORT="SHORT"

class MarketSnapshot(FrozenModel):
    snapshot_id: UUID
    instrument: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    observed_at: datetime
    close: Decimal
    sequence: int = Field(ge=0)
    data_hash: str = Field(pattern=r"^[0-9a-fA-F]{64}$")

class SMCResult(FrozenModel):
    snapshot_id: UUID
    structure: Literal["HH_HL","LH_LL","RANGE","UNKNOWN"]
    liquidity_swept: bool
    mss_confirmed: bool
    bos_confirmed: bool
    ob_confirmed: bool
    fvg_confirmed: bool
    provenance_snapshot_id: UUID

class SignalCandidate(FrozenModel):
    signal_id: UUID = Field(default_factory=uuid4)
    snapshot_id: UUID
    side: SignalSide
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    rationale: str = Field(min_length=1, max_length=2000)

class TradeIntent(FrozenModel):
    intent_id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    snapshot_id: UUID
    side: SignalSide
    entry: Decimal = Field(gt=0)
    stop_loss: Decimal = Field(gt=0)
    take_profit: Decimal = Field(gt=0)
    contracts: Decimal = Field(gt=0)
    @model_validator(mode="after")
    def prices_valid(self):
        if self.side is SignalSide.LONG and not (self.stop_loss < self.entry < self.take_profit):
            raise ValueError("LONG requires stop < entry < take_profit")
        if self.side is SignalSide.SHORT and not (self.take_profit < self.entry < self.stop_loss):
            raise ValueError("SHORT requires take_profit < entry < stop")
        return self

class RiskProposal(FrozenModel):
    intent_id: UUID
    risk_pct: Decimal = Field(gt=0, le=Decimal("1"))
    max_loss: Decimal = Field(gt=0)
    notional: Decimal = Field(gt=0)
    sizing_method: Literal["DECIMAL_FAIL_CLOSED"] = "DECIMAL_FAIL_CLOSED"

class RiskGateDecision(FrozenModel):
    intent_id: UUID
    allowed: bool
    reason: str = Field(min_length=1)
    checked_at: datetime

class Approval(FrozenModel):
    intent_id: UUID
    approval_id: UUID = Field(default_factory=uuid4)
    approved: bool
    approver: Literal["SYSTEM_POLICY"] = "SYSTEM_POLICY"
    risk_gate_allowed: bool

class OrderFilled(FrozenModel):
    fill_id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    order_id: str = Field(min_length=1)
    fill_price: Decimal = Field(gt=0)
    fill_size: Decimal = Field(gt=0)
    fees: Decimal = Field(ge=0)
    fee_currency: str = Field(min_length=1)
    maker: bool
    execution_mode: Literal["MOCK","OKX_DEMO"]
