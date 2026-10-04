from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from .agent_role import AgentRole
class AgentEvent(BaseModel):
    model_config=ConfigDict(extra="forbid", frozen=True)
    event_id:UUID
    event_type:str=Field(min_length=1,max_length=128)
    schema_version:str=Field(min_length=1,max_length=32)
    producer_agent_id:str=Field(min_length=1,max_length=128)
    producer_role:AgentRole
    correlation_id:UUID
    causation_id:UUID|None=None
    task_id:UUID
    timestamp:datetime
    artifact_refs:list[str]=Field(default_factory=list,max_length=256)
    payload_hash:str=Field(pattern=r"^[0-9a-fA-F]{64}$")
    payload_type:str=Field(min_length=1,max_length=128)
