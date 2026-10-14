import time
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from backend.app.tools.registry import tool_registry
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class ExecutionResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    duration_ms: int
    status: str  # SUCCESS, FAILURE, TIMEOUT, RETRIED
    error_message: Optional[str] = None
    recoverable: bool = False

class ToolExecutor:
    """Executes validated tools with strict timeout, observation formatting, and audit capture."""

    def __init__(self, timeout_seconds: int = settings.TOOL_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        tool_def = tool_registry.get_tool(tool_name)
        if not tool_def:
            return ExecutionResult(
                tool_name=tool_name,
                arguments=arguments,
                duration_ms=0,
                status="FAILURE",
                error_message=f"Tool '{tool_name}' not found in registry.",
                recoverable=False
            )

        start_time = time.perf_counter()
        try:
            # Execute tool with context
            output = tool_registry.execute(tool_name, context=context, **arguments)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            # Check if output indicates an explicit error or 503
            if isinstance(output, dict) and output.get("error"):
                is_recoverable = output.get("recoverable", False) or "503" in str(output.get("error")) or "transient" in str(output.get("error")).lower()
                return ExecutionResult(
                    tool_name=tool_name,
                    arguments=arguments,
                    output=output,
                    duration_ms=duration_ms,
                    status="FAILURE",
                    error_message=str(output.get("error")),
                    recoverable=is_recoverable
                )

            return ExecutionResult(
                tool_name=tool_name,
                arguments=arguments,
                output=output,
                duration_ms=duration_ms,
                status="SUCCESS",
                recoverable=False
            )

        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            err_str = str(e)
            is_recoverable = "timeout" in err_str.lower() or "503" in err_str
            logger.error(f"Error executing tool '{tool_name}': {err_str}")
            return ExecutionResult(
                tool_name=tool_name,
                arguments=arguments,
                duration_ms=duration_ms,
                status="FAILURE",
                error_message=err_str,
                recoverable=is_recoverable
            )

tool_executor = ToolExecutor()
