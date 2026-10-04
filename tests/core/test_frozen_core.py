from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from ai_trading_agent.core import *
from ai_trading_agent.core.llm_boundary import LLMAdvisorBoundary, LLMExecutionBoundaryError

def fixture_chain():
    sid=uuid4()
    snap=MarketSnapshot(snapshot_id=sid,instrument="BTC-USDT-SWAP",timeframe="15m",observed_at=datetime.now(timezone.utc),close=Decimal("60000"),sequence=1,data_hash="a"*64)
    smc=SMCResult(snapshot_id=sid,structure="HH_HL",liquidity_swept=True,mss_confirmed=True,bos_confirmed=True,ob_confirmed=True,fvg_confirmed=True,provenance_snapshot_id=sid)
    sig=SignalCandidate(snapshot_id=sid,side="LONG",confidence=Decimal("0.85"),rationale="confirmed structure")
    return snap,smc,sig

def test_canonical_flow_and_fill():
    snap,smc,sig=fixture_chain()
    orch=FrozenCoreOrchestrator(RiskGate(),MockExecutionPort())
    intent=orch.propose(snap,smc,sig,Decimal("60000"),Decimal("59000"),Decimal("62000"),Decimal("1"),Decimal("0.005"),Decimal("50"),Decimal("60000"))
    proposal=RiskProposal(intent_id=intent.intent_id,risk_pct=Decimal("0.005"),max_loss=Decimal("50"),notional=Decimal("60000"))
    approval=orch.approve(intent,proposal)
    assert approval.approved and approval.risk_gate_allowed
    fill=orch.execute(intent,approval)
    assert fill.fill_price==intent.entry and fill.fill_size==intent.contracts

def test_risk_gate_fails_closed_above_limit():
    snap,smc,sig=fixture_chain(); orch=FrozenCoreOrchestrator(RiskGate(),MockExecutionPort())
    intent=orch.propose(snap,smc,sig,Decimal("60000"),Decimal("59000"),Decimal("62000"),Decimal("1"),Decimal("0.02"),Decimal("200"),Decimal("60000"))
    proposal=RiskProposal(intent_id=intent.intent_id,risk_pct=Decimal("0.02"),max_loss=Decimal("200"),notional=Decimal("60000"))
    approval=orch.approve(intent,proposal)
    assert not approval.approved
    with pytest.raises(PermissionError): orch.execute(intent,approval)

def test_provenance_mismatch_rejected():
    snap,smc,sig=fixture_chain(); bad=SignalCandidate(snapshot_id=uuid4(),side="LONG",confidence=Decimal("0.8"),rationale="bad")
    with pytest.raises(ValueError): FrozenCoreOrchestrator(RiskGate(),MockExecutionPort()).propose(snap,smc,bad,Decimal("60000"),Decimal("59000"),Decimal("62000"),Decimal("1"),Decimal("0.005"),Decimal("50"),Decimal("60000"))

def test_llm_cannot_execute():
    with pytest.raises(LLMExecutionBoundaryError): LLMAdvisorBoundary().validate_action("EXECUTE")
