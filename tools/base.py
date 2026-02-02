from __future__ import annotations
import abc
from enum import Enum
from pydantic import BaseModel,ValidationError
from typing import Any,Optional
from dataclasses import dataclass,field
from pathlib import Path
from pydantic.json_schema import model_json_schema

class ToolKind(str, Enum):
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    NETWORK = "network"
    MEMORY = "memory"
    MCP = "mcp"

@dataclass
class ToolInvocation:
    cwd : Path
    params : dict[str, any]

@dataclass
class ToolResult:
    success : bool
    output : str
    error : Optional[str] = None
    metadata : dict[str, Any] = field(default_factory = dict)

@dataclass
class ToolConfirmation:
    tool_name : str
    params : dict[str, Any]
    description : str


class Tool(abc.ABC):
    name : str = "base_tool"
    desc : str = "Base Tool"
    kind : ToolKind = ToolKind.READ

    def __init__(self) -> None:
        pass

    @property
    def schema(self) -> dict[str, Any] | type['BaseModel']:
        raise NotImplementedError("Tool must define schema ie override this method")
        
    @abc.abstractmethod
    async def execute(self, invocation : ToolInvocation) -> ToolResult:
        pass

    def validate_params(self, params : dict[str, Any]) -> list[str]:
        schema = self.schema
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                BaseModel(**params)
            except ValidationError as e:
                errors = []
                for error in e.errors:
                    field = '.'.join(str(x) for x in error.get("loc",[]))
                    msg = error.get("msg", "Validation Error")
                    errors.append(f"Parameter '{field}' : {msg}")
                
                return errors
            except Exception as e:
                return [str(e)]
        
        return []
    
    def is_mutating(self, params : dict[str, Any]) -> bool:
        return self.kind in {
            ToolKind.WRITE,
            ToolKind.SHELL,
            ToolKind.NETWORK,
            ToolKind.MEMORY
        }
    
    async def get_confirmation(self, invocation : ToolInvocation) -> ToolInvocation | None:
        if not self.is_mutating(invocation.params):
            return None
        
        return ToolConfirmation(
            tool_name = self.name,
            params = invocation.params,
            description = f"Execute {self.name}"
        )
    
    def to_openai_schema(self) -> dict[str, Any]:
        schema = self.schema

        if isinstance(schema, type) and issubclass(schema, BaseModel):

            json_schema = model_json_schema(schema, mode="serialization")

            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                },
            }

        if isinstance(schema, dict):
            result = {
                "name": self.name,
                "description": self.description,
            }

            if "parameters" in schema:
                result["parameters"] = schema["parameters"]
            else:
                result["parameters"] = schema

            return result

        raise ValueError(f"Invalid schema type for tool {self.name}: {type(schema)}")
