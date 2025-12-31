import logging
from typing import Optional
from uuid import UUID

from app.orm.session import SessionOrm
from app.repository.session import SessionRepository
from app.services.system.exceptions import InternalError, NotFoundError
from app.schemas.domain.session import SessionDTO, SessionCreateDTO
from app.services.external.openai import ChatCompletionProvider


logger = logging.getLogger(__name__)

class SessionService:
    """Service class for managing session operations."""

    @classmethod
    async def create(cls, data: SessionCreateDTO) -> SessionDTO:
        """Create a new session for the user and return it with extended information."""
        try:
            session_orm = SessionOrm(**data.model_dump())
            session = await SessionRepository.create(session_orm)     
            return SessionDTO.model_validate(session)
        except Exception as e:
            logger.exception(f"LOGGER:Failed to create session for data ={data}: {e}")
            raise InternalError("Failed to create session")

    @classmethod
    async def get_or_create_for_user(cls, user_id: UUID) -> SessionDTO:
        """Get or create a session for the user."""
        try:
            session = await SessionRepository.retrieve_by_user_id(user_id)
            if not session:
                ai_thread = await ChatCompletionProvider.create_thread()
                session_data = SessionCreateDTO(user_id=user_id, provider_thread_id=ai_thread.id)
                session = await cls.create(session_data)
            return SessionDTO.model_validate(session)
        except Exception as e:
            logger.exception(f"LOGGER:Failed to get or create session for user_id={user_id}: {e}")
            raise InternalError("Failed to get or create session")