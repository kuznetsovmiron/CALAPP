import logging
import parsedatetime
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import List
from zoneinfo import ZoneInfo
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
            start_dt, end_dt = await cls._resolve_event_time(
                time_expression=command.time_expression,
                duration_minutes=command.duration_minutes,
                timezone_str="Europe/Moscow",
            )
            events = GoogleEventService.list_events(
                creds, command.limit, start_dt, end_dt, order_by="startTime"
            )
            return [await cls._convert_to_dto(e) for e in events]
        except Exception:
            logger.exception("Failed to list events")
            raise InternalError("Failed to list events")

    @classmethod
    async def create_event(cls, user_id: UUID, command: EventCreateCommand) -> EventDTO:
        try:
            creds = await cls._get_fresh_creds_for_user(user_id)
            start_dt, end_dt = await cls._resolve_event_time(
                time_expression=command.time_expression,
                duration_minutes=command.duration_minutes or 60,
                timezone_str="Europe/Moscow",
            )
            payload = cls._build_payload(command, start_dt, end_dt)
            event = GoogleEventService.create_event(creds, payload)
            return await cls._convert_to_dto(event)
        except Exception:
            logger.exception("Failed to create event")
            raise InternalError("Failed to create event")

    @classmethod
    async def update_event(cls, user_id: UUID, event_id: str, command: EventUpdateCommand) -> EventDTO:
        try:
            creds = await cls._get_fresh_creds_for_user(user_id)
            start_dt = end_dt = None
            if command.time_expression:
                start_dt, end_dt = await cls._resolve_event_time(
                    time_expression=command.time_expression,
                    duration_minutes=command.duration_minutes or 60,
                    timezone_str="Europe/Moscow",
                )
            payload = cls._build_payload(command, start_dt, end_dt)
            if not payload:
                raise InternalError("No fields to update")
            event = GoogleEventService.update_event(creds, event_id, payload)
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
    def _build_payload(command: EventCreateCommand | EventUpdateCommand, start_dt: datetime | None = None, end_dt: datetime | None = None) -> dict:
        payload = {}
        if getattr(command, "title", None) is not None:
            payload["summary"] = command.title
        if getattr(command, "description", None) is not None:
            payload["description"] = command.description
        if getattr(command, "location", None) is not None:
            payload["location"] = command.location
        if getattr(command, "attendees", None) is not None:
            payload["attendees"] = [{"email": a} for a in command.attendees]

        if start_dt and end_dt:
            payload["start"] = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
            payload["end"] = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}

        return payload

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
            if creds.expiry and creds.expiry.tzinfo is None:
                creds.expiry = creds.expiry.replace(tzinfo=timezone.utc)
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

    @staticmethod
    async def _resolve_event_time(time_expression: str, timezone_str: str, duration_minutes: int) -> tuple[datetime, datetime]:
        try:
            cal = parsedatetime.Calendar()
            time_struct, parse_status = cal.parse(time_expression)
            if parse_status == 0:
                raise ValueError(f"Could not parse time expression: {time_expression}")
            start_dt = datetime(*time_struct[:6])
            tz = ZoneInfo(timezone_str)
            start_dt = start_dt.replace(tzinfo=tz).astimezone(timezone.utc)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            logger.warning(f"\nLOGGER: Resolved event time: {start_dt} - {end_dt}")
            return start_dt, end_dt
        except ValueError:
            raise
        except Exception:
            logger.error("Failed to resolve event time")
            raise InternalError(f"Failed to resolve event time for expression: {time_expression}")