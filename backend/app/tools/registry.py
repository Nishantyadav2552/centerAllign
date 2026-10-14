from typing import Callable, Dict, Any, List, Optional
from pydantic import BaseModel, Field
import inspect

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    requires_approval: bool = False
    permission: str = "read"  # read, write, sensitive_write
    
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._executors: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        requires_approval: bool = False,
        permission: str = "read"
    ):
        def decorator(func: Callable):
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema,
                requires_approval=requires_approval,
                permission=permission
            )
            self._executors[name] = func
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_catalog(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "requires_approval": t.requires_approval,
                "permission": t.permission
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if name not in self._executors:
            raise ValueError(f"Tool '{name}' is not registered in ToolRegistry.")
        
        executor = self._executors[name]
        return executor(context=context, **kwargs)

tool_registry = ToolRegistry()
