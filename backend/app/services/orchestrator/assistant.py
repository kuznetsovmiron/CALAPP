import logging
from uuid import UUID

from app.services.external.openai import ChatCompletionProvider
from app.services.orchestrator.dispatcher import ToolDispatcher
from app.schemas.orchestrator.assistant import AssistantOutput
from app.schemas.orchestrator.tool import ToolCall

logger = logging.getLogger(__name__)


class AssistantService:
    """Handles user messages, interacts with LLM provider, and executes tools."""

    @classmethod
    async def handle_user_message(cls, user_id: UUID, message: str, thread_id: str, context: str | None = None) -> AssistantOutput:
        """Handles a message from the user."""
        try:
            # Get structured output directly from provider
            output = await ChatCompletionProvider.complete(thread_id, message, context)
            
            # Execute tool if requested
            if output.tool_name:
                # Executes tool
                tool_call = ToolCall(name=output.tool_name, arguments=output.arguments or {})
                print(f"Tool call: {tool_call.model_dump(mode='json', exclude_none=True)}")
                # Dispatch tool call
                result = await ToolDispatcher.dispatch(user_id, tool_call)
                # Send tool result back to provider
                output = await ChatCompletionProvider.submit_tool_result(
                    thread_id=thread_id,
                    tool_call_id=output.tool_call_id,
                    run_id=output.run_id,
                    result=result,
                )

            # Return assistant output
            return output

        except Exception as e:
            logger.exception(f"Assistant error for user {user_id}: {e}")
            return AssistantOutput(
                text="Sorry, something went wrong while processing your request."
            )