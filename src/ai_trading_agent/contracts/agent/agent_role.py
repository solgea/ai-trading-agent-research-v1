from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
class AgentRole(str, Enum):
    ORCHESTRATOR="ORCHESTRATOR"; RESEARCH="RESEARCH"; MARKET_INTELLIGENCE="MARKET_INTELLIGENCE"; SIGNAL="SIGNAL"; LLM_ADVISOR="LLM_ADVISOR"; RISK="RISK"; QA="QA"; EXECUTION="EXECUTION"
class AgentIdentity(BaseModel):
    model_config=ConfigDict(extra="forbid", frozen=True)
    agent_id:str=Field(min_length=1,max_length=128)
    role:AgentRole
    version:str=Field(min_length=1,max_length=32)
