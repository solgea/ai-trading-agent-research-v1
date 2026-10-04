from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from .agent_role import AgentRole
from .agent_permission import AgentPermission
class AgentTaskStatus(str, Enum):
    CREATED="CREATED"; ASSIGNED="ASSIGNED"; RUNNING="RUNNING"; WAITING="WAITING"; VALIDATING="VALIDATING"; COMPLETED="COMPLETED"; FAILED="FAILED"; REJECTED="REJECTED"; BLOCKED="BLOCKED"
class AgentTask(BaseModel):
    model_config=ConfigDict(extra="forbid")
    task_id:UUID
    parent_task_id:UUID|None=None
    team_id:str=Field(min_length=1,max_length=128)
    agent_id:str=Field(min_length=1,max_length=128)
    role:AgentRole
    task_type:str=Field(min_length=1,max_length=128)
    input_artifact_refs:list[str]=Field(default_factory=list,max_length=256)
    required_permissions:list[AgentPermission]=Field(default_factory=list,max_length=64)
    status:AgentTaskStatus=AgentTaskStatus.CREATED
    created_at:datetime
    started_at:datetime|None=None
    completed_at:datetime|None=None
    correlation_id:UUID
    idempotency_key:str=Field(min_length=1,max_length=256)
    expected_result_type:str=Field(min_length=1,max_length=128)
