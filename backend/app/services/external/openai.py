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
        except Exception as e:
            logger.exception(f"Failed to create thread: {e}")
            raise

    @classmethod
    async def submit_tool_result(cls, thread_id: str, tool_call_id: str, run_id: str, result: str | dict) -> AssistantOutput:
        """Submits a tool result to a thread."""
        try:
            # Cancel any active run in the thread
            await cls._cancel_active_run(thread_id)
            # Submit tool outputs
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
            if run.status != "completed":
                raise RuntimeError(f"Run after tool execution is not completed with status: {run.status} and run id: {run_id}")
            # Extract text from messages
            text_array = []
            messages = proxy_client.beta.threads.messages.list(
                thread_id=thread_id,
                run_id=run_id
            )
            for message in reversed(messages.data):
                if message.role == "assistant":
                    for item in message.content:
                        if item.type == "text":
                            text_array.append(item.text.value)
            return AssistantOutput(
                text="\n".join(text_array) if text_array else None
            )

        except Exception as e:
            logger.exception(f"Failed to submit tool result to thread {thread_id} with tool call id {tool_call_id} and result {result}: {e}")
            raise

    @classmethod
    async def complete(cls, thread_id: str, content: str, context: str = None) -> AssistantOutput:
        """Completes the thread and returns the assistant output."""
        try:
            # Cancel any active run in the thread
            await cls._cancel_active_run(thread_id, status=["in_progress", "active", "requires_action"])
            # Add user message to thread
            await cls._add_message(thread_id, content)            
            # Create and poll the run
            run = proxy_client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=AI_ASSISTANT_ID,
                additional_instructions=context
            )            
            # Get messages after run completes
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
                    text="".join(text_array) if text_array else None,
                )
            
            elif run.status == "requires_action":
                tool_call = run.required_action.submit_tool_outputs.tool_calls[0]

                return AssistantOutput(
                    tool_name=tool_call.function.name,
                    tool_call_id=tool_call.id,
                    arguments=json.loads(tool_call.function.arguments),
                    run_id=run.id
                )            
            else:
                raise RuntimeError(f"Run failed with status: {run.status}")         
        except Exception as e:
            logger.exception(f"Error while completing thread {thread_id} with content {content}: {e}")
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
                    logger.warning(f"Cancelled active run {run.id} in thread {thread_id}")
        except Exception as e:
            logger.exception(f"Failed to cancel active runs in thread {thread_id}: {e}")
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
        except Exception as e:
            logger.exception(f"Failed to add message to thread {thread_id} with content {content}: {e}")
            raise