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
from app.schemas.external.google import GoogleEvent, GoogleEventDateTime, GoogleEventAttendee, GoogleEventCreate


logger = logging.getLogger(__name__)

class EventService:
    """Service class for managing event operations."""

    @classmethod
    async def list_events(cls, user_id: UUID, command: EventListCommand) -> List[EventDTO]:
        """List events for a user."""
        try:
            # Fetch token from the database and update if necessary
            creds = await cls._get_fresh_creds_for_user(user_id)
            
            # Resolve event time 
            start_dt, end_dt = await cls._resolve_event_time(
                time_expression=command.time_expression,
                duration_minutes=command.duration_minutes,
                timezone_str="Europe/Moscow",
            )
            
            # List events and return results
            events = GoogleEventService.list_events(creds, command.limit, start_dt, end_dt, order_by="startTime")            
            return [await cls._google_to_api(e) for e in events]
        except Exception as e:
            logger.exception(f"Failed to list events")
            raise InternalError("Failed to list events")

    @classmethod
    async def create_event(cls, user_id: UUID, command: EventCreateCommand) -> EventDTO:
        """Create event for a user."""
        try:
            # Fetch fresh credentials for the user
            creds = await cls._get_fresh_creds_for_user(user_id)
            
            # Transform command to Google event
            start_dt, end_dt = await cls._resolve_event_time(
                time_expression=command.time_expression,
                duration_minutes=command.duration_minutes,
                timezone_str="Europe/Moscow",
            )
            attendees = [GoogleEventAttendee(email=a) for a in command.attendees] if command.attendees else None
            
            # Create Google event and return result
            google_event = GoogleEventCreate(
                summary=command.title,
                description=command.description,
                start=GoogleEventDateTime(dateTime=start_dt),
                end=GoogleEventDateTime(dateTime=end_dt),
                location=command.location,
                attendees=attendees,
            )            
            event = GoogleEventService.create_event(creds, google_event)
            return await cls._google_to_api(event)
        except Exception as e:
            logger.exception(f"Failed to create event")
            raise InternalError("Failed to create event")

    @classmethod
    async def update_event(cls, user_id: UUID, event_id: str, command: EventUpdateCommand) -> EventDTO:
        """Update event for a user."""
        try:
            # Fetch fresh credentials for the user
            creds = await cls._get_fresh_creds_for_user(user_id)

            update_body: dict = {}

            # Resolve time if provided
            if command.time_expression:
                start_dt, end_dt = await cls._resolve_event_time(
                    time_expression=command.time_expression,
                    duration_minutes=command.duration_minutes or 60,
                    timezone_str="Europe/Moscow",
                )
                update_body["start"] = {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "UTC",
                }
                update_body["end"] = {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "UTC",
                }

            if command.title is not None:
                update_body["summary"] = command.title

            if command.description is not None:
                update_body["description"] = command.description

            if command.location is not None:
                update_body["location"] = command.location

            if command.attendees is not None:
                update_body["attendees"] = [
                    {"email": email} for email in command.attendees
                ]

            if not update_body:
                raise InternalError("No fields to update")

            event = GoogleEventService.update_event(
                creds=creds,
                event_id=event_id,
                update_body=update_body,
            )

            return await cls._google_to_api(event)

        except InternalError:
            raise
        except Exception:
            logger.exception("Failed to update event")
            raise InternalError("Failed to update event")

    @classmethod
    async def delete_event(cls, user_id: UUID, event_id: str) -> bool:
        """Delete event for a user."""
        try:
            # Fetch token from the database
            creds = await cls._get_fresh_creds_for_user(user_id)
            
            # Delete event
            status = GoogleEventService.delete_event(creds, event_id)
            return status
        except Exception as e:
            logger.exception(f"Failed to delete event")
            raise InternalError("Failed to delete event")

    @staticmethod
    async def _google_to_api(event: GoogleEvent) -> EventDTO:
        try:
            # Parse Google event datetime
            def parse_google_dt(gdt: GoogleEventDateTime) -> datetime:
                if gdt.dateTime:
                    return gdt.dateTime
                # all-day event → midnight UTC
                return datetime.fromisoformat(gdt.date).replace(tzinfo=timezone.utc)

            # Return API event
            return EventDTO(
                id=event.id,
                title=event.summary,
                description=event.description,
                start_dt=parse_google_dt(event.start),
                end_dt=parse_google_dt(event.end),
                location=event.location,
                attendees=[a.email for a in (event.attendees or [])],
            )
        except Exception as e:
            logger.exception(f"Failed to convert Google event to API event: {e}")
            raise InternalError("Failed to convert Google event to API event")

    @classmethod
    async def _get_fresh_creds_for_user(cls, user_id: UUID) -> Credentials:
        """Get fresh credentials for a user."""
        try:
            # Fetch token from the database
            token = await TokenRepository.retrieve_by_user_id(user_id)
            if not token:
                raise InternalError("Token not found")
            creds = GoogleAuthService.get_fresh_creds(token)
            
            # Normalize Google creds expiry
            creds_expiry = creds.expiry
            if creds_expiry and creds_expiry.tzinfo is None:
                creds_expiry = creds_expiry.replace(tzinfo=timezone.utc)            
            
            # Compare with current token expiry and update if necessary
            if creds.token != token.access_token or creds_expiry != token.expiry:      
                setattr(token, "access_token", creds.token)
                setattr(token, "expiry", creds_expiry)
                await TokenRepository.update(token)            
            return creds
        except InternalError:
            raise
        except Exception as e:
            logger.exception(f"Failed to get fresh credentials for user")
            raise InternalError("Failed to get fresh credentials for user")

    @staticmethod
    async def _resolve_event_time(time_expression: str, timezone_str: str, duration_minutes: int) -> tuple[datetime, datetime]:
        """Resolves a human time expression into start and end datetimes (UTC)."""
        try:
            # Initialize parsedatetime Calendar
            cal = parsedatetime.Calendar()

            # Parse the time expression
            time_struct, parse_status = cal.parse(time_expression)
            if parse_status == 0:
                raise ValueError(f"Could not parse time expression: {time_expression}")

            # Convert time_struct to datetime
            start_dt = datetime(*time_struct[:6])

            # Localize to user timezone and convert to UTC
            tz = ZoneInfo(timezone_str)
            start_dt = start_dt.replace(tzinfo=tz).astimezone(timezone.utc)

            # Calculate end time
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            # Log for debugging
            logger.warning(f"\nLOGGER: Resolved event time: {start_dt} - {end_dt}")
            return start_dt, end_dt
        except Exception as e:
            logger.error(f"Failed to resolve event time")
            raise InternalError("Failed to resolve event time")