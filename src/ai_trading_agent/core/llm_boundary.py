class LLMExecutionBoundaryError(PermissionError): pass

class LLMAdvisorBoundary:
    """LLM may advise; it can never approve or execute."""
    FORBIDDEN = frozenset({"EXECUTE", "APPROVE", "SUBMIT_ORDER"})
    def validate_action(self, action: str) -> None:
        if action in self.FORBIDDEN:
            raise LLMExecutionBoundaryError(f"LLM action forbidden: {action}")
