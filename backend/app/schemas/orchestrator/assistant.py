from pydantic import BaseModel


class AssistantOutput(BaseModel):
    """Normalized assistant response: either plain text or a tool invocation."""
    text: str | None = None
    run_id: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    arguments: dict | None = None    
