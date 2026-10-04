from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from .agent_role import AgentRole
class AgentResultStatus(str, Enum):
    SUCCESS="SUCCESS"; PARTIAL="PARTIAL"; FAILED="FAILED"; REJECTED="REJECTED"
class AgentResult(BaseModel):
    model_config=ConfigDict(extra="forbid")
    result_id:UUID
    task_id:UUID
    agent_id:str=Field(min_length=1,max_length=128)
    role:AgentRole
    status:AgentResultStatus
    result_type:str=Field(min_length=1,max_length=128)
    artifact_refs:list[str]=Field(default_factory=list,max_length=256)
    emitted_event_ids:list[UUID]=Field(default_factory=list,max_length=256)
    validation_passed:bool
    validation_errors:list[str]=Field(default_factory=list,max_length=256)
    created_at:datetime
    correlation_id:UUID
