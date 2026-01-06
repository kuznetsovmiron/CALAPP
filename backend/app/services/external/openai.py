import openai
import logging
import json
from typing import Literal, Optional
from openai.types.beta import Thread
from app.schemas.orchestrator.assistant import AssistantOutput
from app.core.config import AI_KEY, AI_ASSISTANT_ID


logger = logging.getLogger(__name__)

proxy_client = openai.Client(
    api_key=AI_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)

class ChatCompletionProvider:
    """Provides chat completion functionality using OpenAI API."""

    @classmethod
    async def create_thread(cls) -> Thread:
        """Creates a new thread."""
        try:
            thread = proxy_client.beta.threads.create()
            return thread
        except Exception:
            logger.exception("Failed to create thread")
            raise

    @classmethod
    async def complete(cls, thread_id: str, content: str, context: str = None) -> AssistantOutput:
        """Completes the thread and returns the assistant output."""
        try:
            # Cancel any active run in the thread
            await cls._cancel_active_run(thread_id, status=["in_progress", "active", "requires_action"])
            
            # Add user message to thread and create and poll the run
            await cls._add_message(thread_id, content)            
            run = proxy_client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=AI_ASSISTANT_ID,
                additional_instructions=context
            )            

            # Handle run result
            return await cls._handle_run_result(thread_id, run)
        except Exception:
            logger.exception(f"Failed to complete thread {thread_id} with content {content}")
            raise

    @classmethod
    async def submit_tool_result(cls, thread_id: str, tool_call_id: str, run_id: str, result: str | dict) -> AssistantOutput:
        """Submits a tool result to a thread."""
        try:
            # Add tool outputs to run
            proxy_client.beta.threads.runs.submit_tool_outputs(
                run_id=run_id,
                thread_id=thread_id,
                tool_outputs=[
                    {                        
                        "tool_call_id": tool_call_id, 
                        "output": json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)
                    }
                ],
            )

            # Poll until run is completed
            run = proxy_client.beta.threads.runs.poll(
                thread_id=thread_id,
                run_id=run_id
            )

            # Handle run result
            return await cls._handle_run_result(thread_id, run)
        except Exception:
            logger.exception(f"Failed to submit tool result to thread {thread_id} with tool call id {tool_call_id} and result {result}")
            raise

    @classmethod
    async def _handle_run_result(cls, thread_id: str, run) -> AssistantOutput:
        """Handles the run result and returns the assistant output."""
        try:
            # Handle completed run
            if run.status == "completed":
                messages = proxy_client.beta.threads.messages.list(
                    thread_id=thread_id,
                    run_id=run.id
                )
                text_array = []
                for message in reversed(messages.data):
                    if message.role == "assistant":
                        for item in message.content:
                            if item.type == "text":
                                text_array.append(item.text.value)

                return AssistantOutput(
                    text="\n".join(text_array) if text_array else None
                )

            # Handle requires action run
            if run.status == "requires_action":
                tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
                return AssistantOutput(
                    tool_name=tool_call.function.name,
                    tool_call_id=tool_call.id,
                    arguments=json.loads(tool_call.function.arguments),
                    run_id=run.id
                )

            # Handle failed, cancelled, expired runs and unexpected status
            if run.status in ("failed", "cancelled", "expired"):
                raise RuntimeError(f"Run failed with status: {run.status}")
            else:
                raise RuntimeError(f"Unexpected run status: {run.status}")
        except Exception:
            logger.exception(f"Failed to handle run result for thread {thread_id} with run {run}")
            raise

    @classmethod
    async def _cancel_active_run(cls, thread_id: str, status: Optional[Literal["active", "in_progress", "completed", "requires_action"]] = ["active", "in_progress"]):
        """Cancel any active run in the thread."""
        try:
            runs = proxy_client.beta.threads.runs.list(thread_id=thread_id)
            for run in runs.data:
                if run.status in status:
                    proxy_client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    logger.warning(f" Cancelled active run {run.id} in thread {thread_id}")
        except Exception:
            logger.exception(f"Failed to cancel active runs in thread {thread_id}")
            raise

    @classmethod
    async def _add_message(cls, thread_id: str, content: str):
        """Adds a message to a thread."""
        try:
            proxy_client.beta.threads.messages.create(
                thread_id=thread_id,
                content=content,
                role="user"
            )
        except Exception:
            logger.exception(f"Failed to add message to thread {thread_id} with content {content}")
            raise