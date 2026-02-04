from __future__ import annotations
from tools.base import Tool,ToolResult,ToolInvocation
from tools.builtin.read_file import ReadFileTool 
from typing import Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        self._tools : dict[str, Tool] = {}
    
    def register(self, tool : Tool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.name}")
        self._tools[tool.name] = tool
    
    def unregister(self, name : str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        
        return False
    
    def get(self, name : str) -> Tool | None:
        if name in self._tools:
            return self._tools[name]
        return None 

    def get_tools(self) -> list[Tool]:
        tools : list[Tool] = []

        for tool in self._tools.values():
            tools.append(tool)
        
        return tools
    
    def get_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.get_tools()]
    
    
    async def invoke(
        self,
        name: str,
        params: dict[str, Any],
        cwd: Path,
    ) -> ToolResult:
        
        tool = self.get(name)
        if tool is None:
            result = ToolResult.error_result(
                f"Unknown tool: {name}",
                metadata={"tool_name": name},
            )


        validation_errors = tool.validate_params(params)
        if validation_errors:
            result = ToolResult.error_result(
                f"Invalid parameters: {'; '.join(validation_errors)}",
                metadata={
                    "tool_name": name,
                    "validation_errors": validation_errors,
                },
            )

        invocation = ToolInvocation(
            cwd = cwd,
            params=params
        )
        
        try:
            await tool.execute(invocation)
        except Exception as e:
            logger.exception(f"Tool {name} raised unexpected error")
            return ToolResult.error_result(
                f"Internal error: {str(e)}",
                metadata={
                    "tool_name",
                    name,
                },
            )
    
def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    BUILT_IN_TOOLS = [ReadFileTool]

    for tool_class in BUILT_IN_TOOLS:
        registry.register(tool_class())
    
    return registry