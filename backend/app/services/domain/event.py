import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import List
from google.oauth2.credentials import Credentials

from app.repository.token import TokenRepository
from app.services.system.exceptions import InternalError
from app.services.external.google import GoogleEventService, GoogleAuthService
from app.schemas.domain.event import EventCreateCommand, EventDTO, EventListCommand, EventUpdateCommand
from app.schemas.external.google import GoogleEvent

logger = logging.getLogger(__name__)


class EventService:
    """Service class for managing event operations."""

    @classmethod
    async def list_events(cls, user_id: UUID, command: EventListCommand) -> List[EventDTO]:
        try:
            creds = await cls._get_fresh_creds_for_user(user_id)
            events = GoogleEventService.list_events(creds, command.limit, command.start_dt, command.end_dt, order_by="startTime")
            return [await cls._convert_to_dto(e) for e in events]
        except Exception:
            logger.exception("Failed to list events")
            raise InternalError("Failed to list events")

    @classmethod
    async def get_event(cls, user_id: UUID, event_id: str) -> EventDTO:
        try:
            creds = await cls._get_fresh_creds_for_user(user_id)
            event = GoogleEventService.get_event(creds, event_id)
            return await cls._convert_to_dto(event)
        except Exception:
            logger.exception("Failed to get event")
            raise InternalError("Failed to get event")

    @classmethod
    async def create_event(cls, user_id: UUID, command: EventCreateCommand) -> EventDTO:
        try:
            creds = await cls._get_fresh_creds_for_user(user_id)    
            event = GoogleEventService.create_event(creds, command.model_dump(exclude_none=True))
            return await cls._convert_to_dto(event)
        except Exception:
            logger.exception("Failed to create event")
            raise InternalError("Failed to create event")

    @classmethod
    async def update_event(cls, user_id: UUID, event_id: str, command: EventUpdateCommand) -> EventDTO:
        try:
            creds = await cls._get_fresh_creds_for_user(user_id)
            event = GoogleEventService.update_event(creds, event_id, command.model_dump(exclude_none=True))
            return await cls._convert_to_dto(event)
        except InternalError:
            raise
        except Exception:
            logger.exception("Failed to update event")
            raise InternalError("Failed to update event")

    @classmethod
    async def delete_event(cls, user_id: UUID, event_id: str) -> bool:
        try:
            creds = await cls._get_fresh_creds_for_user(user_id)
            return GoogleEventService.delete_event(creds, event_id)
        except Exception:
            logger.exception("Failed to delete event")
            raise InternalError("Failed to delete event")

    @staticmethod
    async def _convert_to_dto(event: GoogleEvent) -> EventDTO:
        try:
            def parse_google_dt(gdt):
                if getattr(gdt, "dateTime", None):
                    return gdt.dateTime
                return datetime.fromisoformat(gdt.date).replace(tzinfo=timezone.utc)

            return EventDTO(
                id=event.id,
                title=event.summary,
                description=event.description,
                start_dt=parse_google_dt(event.start),
                end_dt=parse_google_dt(event.end),
                location=event.location,
                attendees=[a.email for a in (event.attendees or [])],
            )
        except Exception:
            logger.exception("Failed to convert Google event to API event")
            raise InternalError("Failed to convert Google event to API event")

    @classmethod
    async def _get_fresh_creds_for_user(cls, user_id: UUID) -> Credentials:
        try:
            token = await TokenRepository.retrieve_by_user_id(user_id)
            if not token:
                raise InternalError("Token not found")
            creds = GoogleAuthService.get_fresh_creds(token)
            if creds.token != token.access_token or creds.expiry != token.expiry:
                token.access_token = creds.token
                token.expiry = creds.expiry
                await TokenRepository.update(token)
            return creds
        except InternalError:
            raise
        except Exception:
            logger.exception("Failed to get fresh credentials for user")
            raise InternalError("Failed to get fresh credentials for user")
