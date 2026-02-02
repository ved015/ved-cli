from __future__ import annotations
import abc
from enum import Enum
from pydantic import BaseModel
from typing import Any,Optional
from dataclasses import dataclass,field
from pathlib import Path

class ToolKind(str, Enum):
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    "NETWORK" = "network"
    "MEMORY" = "memory"
    "MCP" = "mcp"

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