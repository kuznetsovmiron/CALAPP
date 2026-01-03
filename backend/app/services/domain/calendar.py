import logging
import dateparser
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import List, Literal

from app.orm.token import TokenOrm
from app.repository.token import TokenRepository
from app.schemas.domain.token import TokenProviderEnum
from app.services.system.exceptions import InternalError
from app.services.external.google import GoogleCalService, GoogleAuthService
from app.schemas.domain.calendar import EventCreateCommand, EventDTO, EventListCommand, EventUpdateCommand
from app.schemas.external.google import GoogleEvent, GoogleEventDateTime, GoogleEventAttendee, GoogleEventCreate
from google.oauth2.credentials import Credentials



logger = logging.getLogger(__name__)

class CalendarService:
    """Service class for managing calendar operations."""

    @classmethod
    async def request_token(cls, user_id: UUID) -> str:
        """Request a token from Google for the current user."""
        try:
            flow = GoogleAuthService.get_flow()
            url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
                state=str(user_id)
            )
            logger.info(f"LOGGER: Request token from Google: {url}")
            return url
        except Exception as e:
            logger.exception(f"LOGGER:Failed to request token from Google: {e}", exc_info=e)
            raise InternalError("Failed to request token from Google")

    @classmethod
    async def fetch_token(cls, url: str, state: str):
        """Fetch token from Google."""
        try:
            # Fetch token and user_id from Google
            flow = GoogleAuthService.get_flow()
            flow.fetch_token(authorization_response=str(url))
            creds = flow.credentials     
            # Normalize Google creds expiry
            creds_expiry = creds.expiry
            if creds_expiry and creds_expiry.tzinfo is None:
                creds_expiry = creds_expiry.replace(tzinfo=timezone.utc)            
            # Fetch user_id from state
            user_id = UUID(state)
            if not user_id:
                raise InternalError("User ID not found in state")
            # Store token in the database
            token_orm = TokenOrm(
                user_id=user_id,
                provider=TokenProviderEnum.google,
                access_token=creds.token,
                refresh_token=creds.refresh_token,
                expiry=creds_expiry
            )
            await TokenRepository.create(token_orm)
        except Exception as e:
            logger.exception(f"LOGGER:Failed to store token in the database: {e}", exc_info=e)
            raise InternalError("Failed to store token in the database")

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
            events = GoogleCalService.list_events(creds, command.limit, start_dt, end_dt, order_by="startTime")            
            return [await cls._google_to_api(e) for e in events]
        except Exception as e:
            logger.exception(f"LOGGER:Failed to list events: {e}", exc_info=e)
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
            event = GoogleCalService.create_event(creds, google_event)
            return await cls._google_to_api(event)
        except Exception as e:
            logger.exception(f"LOGGER:Failed to create event: {e}", exc_info=e)
            raise InternalError("Failed to create event")

    @classmethod
    async def update_event(cls, user_id: UUID, event_id: str, command: EventUpdateCommand) -> EventDTO:
        """Update event for a user."""
        try:
            # Fetch token from the database
            creds = await cls._get_fresh_creds_for_user(user_id)
            
            # Update event
            event = GoogleCalService.update_event(creds, event_id, command)
            return await cls._google_to_api(event)
        except Exception as e:
            logger.exception(f"LOGGER:Failed to update event: {e}", exc_info=e)
            raise InternalError("Failed to update event")

    @classmethod
    async def delete_event(cls, user_id: UUID, event_id: str) -> bool:
        """Delete event for a user."""
        try:
            # Fetch token from the database
            creds = await cls._get_fresh_creds_for_user(user_id)
            
            # Delete event
            status = GoogleCalService.delete_event(creds, event_id)
            return status
        except Exception as e:
            logger.exception(f"LOGGER:Failed to delete event: {e}", exc_info=e)
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
            logger.exception(f"LOGGER:Failed to convert Google event to API event: {e}")
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
            logger.exception(f"LOGGER:Failed to get fresh credentials for user: {e}", exc_info=e)
            raise InternalError("Failed to get fresh credentials for user")

    @staticmethod
    async def _resolve_event_time(time_expression: str, timezone_str: str, duration_minutes: int) -> tuple[datetime, datetime]:
        """Resolves a human time expression into start and end datetimes (UTC)."""
        try:
            # Parse time expression and normalize to UTC
            start_dt = dateparser.parse(
                time_expression,
                settings= {
                    "TIMEZONE": timezone_str,
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "PREFER_DATES_FROM": "future",
                },
                languages=None,  # auto-detect
            )
            if not start_dt:
                raise ValueError(f"Could not parse time expression: {time_expression}")

            # Convert to UTC
            start_dt = start_dt.astimezone(timezone.utc)
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            # Log and return start and end times
            logger.warning(f"\nLOGGER: Resolved event time: {start_dt} - {end_dt}")
            return start_dt, end_dt
        except Exception as e:
            logger.exception(f"LOGGER:Failed to resolve event time: {e}", exc_info=e)
            raise InternalError("Failed to resolve event time")