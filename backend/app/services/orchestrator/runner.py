import logging
from uuid import UUID

from app.services.orchestrator.assistant import AssistantService
from app.schemas.orchestrator.assistant import AssistantOutput
from app.services.domain.session import SessionService  
from app.services.orchestrator.context import build_runtime_context

logger = logging.getLogger(__name__)


class AssistantRunner:
    """Orchestrates a single assistant interaction."""

    @classmethod
    async def run(cls, *, user_id: UUID, message: str) -> AssistantOutput:
        """Runs one assistant interaction turn."""

        # Get or create session (thread)
        session = await SessionService.get_or_create_for_user(user_id)

        # Build runtime context
        runtime_context = build_runtime_context(user_id)

        # Delegate to orchestrator
        assistant_output = await AssistantService.handle_user_message(
            user_id=user_id,
            message=message,
            thread_id=session.provider_thread_id,
            context=runtime_context,
        )

        # Return assistant output
        return assistant_output