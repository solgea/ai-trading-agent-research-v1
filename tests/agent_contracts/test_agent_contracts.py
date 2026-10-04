import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from ai_trading_agent.contracts.agent import AgentEvent,AgentIdentity,AgentPermission,AgentPermissionSet,AgentResult,AgentRole,AgentTask

ROOT=Path(__file__).parents[2]; SCHEMAS=ROOT/"contracts"/"agent"

def test_role_closed_enum():
    AgentIdentity(agent_id="a",role=AgentRole.RESEARCH,version="1.0")
    with pytest.raises(ValidationError): AgentIdentity(agent_id="a",role="NOPE",version="1.0",x=1)

def test_permissions_fail_closed():
    p=AgentPermissionSet(permissions=[AgentPermission.MARKET_READ])
    assert p.allows(AgentPermission.MARKET_READ) and not p.allows(AgentPermission.DEMO_EXECUTION)
    with pytest.raises(ValidationError): AgentPermissionSet(permissions=["EXECUTE"])

def test_task_parent_idempotency_roundtrip():
    raw={"task_id":uuid4(),"parent_task_id":None,"team_id":"research-team","agent_id":"research-1","role":"RESEARCH","task_type":"MARKET_RESEARCH","input_artifact_refs":[],"required_permissions":["MARKET_READ"],"status":"CREATED","created_at":datetime.now(timezone.utc),"started_at":None,"completed_at":None,"correlation_id":uuid4(),"idempotency_key":"task-001","expected_result_type":"RESEARCH_REPORT"}
    x=AgentTask(**raw); x.parent_task_id=uuid4()
    assert AgentTask.model_validate_json(x.model_dump_json()).task_id==x.task_id

def test_event_hash_and_correlation():
    raw={"event_id":uuid4(),"event_type":"AgentTaskCreated","schema_version":"1.0","producer_agent_id":"a","producer_role":"RESEARCH","correlation_id":uuid4(),"causation_id":None,"task_id":uuid4(),"timestamp":datetime.now(timezone.utc),"artifact_refs":[],"payload_hash":"a"*64,"payload_type":"AgentTask"}
    AgentEvent(**raw)
    with pytest.raises(ValidationError): AgentEvent(**{**raw,"payload_hash":"bad"})

def test_result_extra_rejected():
    raw={"result_id":uuid4(),"task_id":uuid4(),"agent_id":"risk-1","role":"RISK","status":"SUCCESS","result_type":"RISK_PROPOSAL","artifact_refs":[],"emitted_event_ids":[],"validation_passed":True,"validation_errors":[],"created_at":datetime.now(timezone.utc),"correlation_id":uuid4()}
    AgentResult(**raw)
    with pytest.raises(ValidationError): AgentResult(**{**raw,"execute":True})

def test_json_schemas_valid_and_closed():
    for path in SCHEMAS.glob("*.schema.json"):
        s=json.loads(path.read_text())
        assert s["$schema"]=="https://json-schema.org/draft/2020-12/schema"
        assert s["additionalProperties"] is False
        Draft202012Validator.check_schema(s)

def test_pydantic_schema_root_closed():
    from ai_trading_agent.contracts.agent import AgentPermissionSet,AgentEvent,AgentResult
    models={"agent_role":AgentIdentity,"agent_permission":AgentPermissionSet,"agent_task":AgentTask,"agent_event":AgentEvent,"agent_result":AgentResult}
    for name,m in models.items():
        assert m.model_json_schema()["additionalProperties"] is False
        fs=json.loads((SCHEMAS/f"{name}.schema.json").read_text())
        gs=m.model_json_schema()
        for k in ("properties","required","$defs"):
            if k in gs: assert fs.get(k)==gs[k]
