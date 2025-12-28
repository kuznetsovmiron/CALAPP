from typing import Any, Dict
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Structured request to execute a tool: produced by the LLM and consumed by ToolDispatcher."""
    name: str = Field(..., description="Tool name to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool call")    