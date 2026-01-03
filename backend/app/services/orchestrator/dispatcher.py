import logging
from uuid import UUID
from typing import Any

from app.schemas.orchestrator.tool import ToolCall
from app.services.orchestrator.registry import TOOL_REGISTRY
from app.services.system.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)


class ToolDispatcher:
    """Dispatches tool calls to the correct handler."""

    @classmethod
    async def dispatch(cls, user_id: UUID, tool_call: ToolCall) -> Any:
        """Execute a tool by name with arguments."""

        try:
            handler = TOOL_REGISTRY.get(tool_call.name)
            if not handler:
                raise ToolExecutionError(f"Unknown tool: {tool_call.name}")            
            logger.warning(f"\nLOGGER: Executing tool: {tool_call.name} for user {user_id}")
            return await handler(user_id=user_id, **tool_call.arguments)
        except ToolExecutionError:
            raise
        except Exception as e:
            logger.exception(f"LOGGER:Failed to execute tool '{tool_call.name}' for user {user_id}: {e}", exc_info=e)
            raise ToolExecutionError(f"Failed to execute tool '{tool_call.name}' for user {user_id}")