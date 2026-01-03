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
            # Start assistant run
            output = await ChatCompletionProvider.complete(thread_id, message, context)
            max_tool_steps = 5
            steps = 0            

            # Handle tool calls iteratively (multi-step tool reasoning)
            while output.tool_name:
                # Safety check infinite loop
                steps += 1
                if steps > max_tool_steps:
                    logger.warning(f"\nLOGGER:Max tool steps reached: {steps}")
                    raise RuntimeError("Max tool steps reached")

                # Create tool call and execute it
                tool_call = ToolCall(
                    name=output.tool_name,
                    arguments=output.arguments or {}
                )
                logger.warning(f"\nLOGGER:Tool call: {tool_call.model_dump(mode='json', exclude_none=True)}")
                result = await ToolDispatcher.dispatch(user_id, tool_call)

                # Submit tool result back to provider and continue the run
                output = await ChatCompletionProvider.submit_tool_result(
                    thread_id=thread_id,
                    tool_call_id=output.tool_call_id,
                    run_id=output.run_id,
                    result=result,
                )

            # Final assistant response (no more tool calls)
            return output

        except Exception as e:
            logger.exception(f"LOGGER:Assistant error for user {user_id}: {e}")
            return AssistantOutput(
                text="Sorry, something went wrong while processing your request."
            )