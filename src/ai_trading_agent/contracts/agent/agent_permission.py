from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
class AgentPermission(str, Enum):
    MARKET_READ="MARKET_READ"; ARTIFACT_READ="ARTIFACT_READ"; ARTIFACT_WRITE="ARTIFACT_WRITE"; RESEARCH_READ="RESEARCH_READ"; RESEARCH_WRITE="RESEARCH_WRITE"; SIGNAL_CREATE="SIGNAL_CREATE"; RISK_PROPOSAL_CREATE="RISK_PROPOSAL_CREATE"; RISK_DECISION_READ="RISK_DECISION_READ"; EVENT_PUBLISH="EVENT_PUBLISH"; EVENT_SUBSCRIBE="EVENT_SUBSCRIBE"; REPLAY_EXECUTE="REPLAY_EXECUTE"; GIT_READ="GIT_READ"; GIT_WRITE="GIT_WRITE"; DEMO_EXECUTION="DEMO_EXECUTION"
class AgentPermissionSet(BaseModel):
    model_config=ConfigDict(extra="forbid", frozen=True)
    permissions:list[AgentPermission]=Field(default_factory=list,max_length=64)
    def allows(self, permission:AgentPermission)->bool: return permission in self.permissions
