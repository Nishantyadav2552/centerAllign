import logging
from typing import Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.executor import ExecutionResult

logger = logging.getLogger(__name__)

class RecoveryManager:
    """Manages bounded retries, error classification, and replanning triggers."""

    def __init__(self, max_retries: int = settings.MAX_RETRIES_PER_ACTION):
        self.max_retries = max_retries

    def evaluate_failure(
        self,
        result: ExecutionResult,
        current_retry_count: int
    ) -> Dict[str, Any]:
        """
        Evaluates a tool execution failure and determines whether to retry, replan, or fail.
        """
        if not result.recoverable:
            return {
                "action": "ABORT",
                "reason": f"Non-recoverable failure in tool '{result.tool_name}': {result.error_message}",
                "retry_allowed": False
            }

        if current_retry_count < self.max_retries:
            return {
                "action": "RETRY",
                "retry_count": current_retry_count + 1,
                "delay_seconds": 1.0 * (2 ** current_retry_count),
                "reason": f"Recoverable error detected ({result.error_message}). Executing bounded retry {current_retry_count + 1}/{self.max_retries}.",
                "retry_allowed": True
            }

        return {
            "action": "REPLAN_OR_FAIL",
            "reason": f"Retry limit exhausted ({self.max_retries} attempts) for tool '{result.tool_name}'.",
            "retry_allowed": False
        }

recovery_manager = RecoveryManager()
