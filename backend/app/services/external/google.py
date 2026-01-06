import logging
from typing import Dict, List, Tuple, Literal, Optional
import httplib2
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource as GoogleResource
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from app.schemas.external.google import GoogleEvent
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, GOOGLE_SCOPES
from app.services.system.exceptions import InternalError
from app.orm.token import TokenOrm


logger = logging.getLogger(__name__)

class GoogleAuthService:
    """Google Authentication service class"""

    @classmethod
    def get_flow(cls) -> Flow:
        """Get flow from client config"""
        try:
            return Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        except Exception:
            logger.exception("Failed to get flow")
            raise InternalError("Failed to get flow")

    @classmethod
    def get_fresh_creds(cls, token: TokenOrm) -> Credentials:
        """Return credentials refreshed if expired and update DB if needed."""
        try:
            # Ensure DB expiry is timezone-aware UTC
            creds = Credentials(
                token=token.access_token,
                refresh_token=token.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=GOOGLE_SCOPES,
                expiry=token.expiry.astimezone(timezone.utc).replace(tzinfo=None)

            )
            # Refresh if expired  
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())  # synchronous call
            return creds       
        except RefreshError:
            raise InternalError("Google authorization expired. Please reconnect your calendar.")
        except Exception:
            logger.exception("Failed to get fresh credentials")
            raise InternalError("Failed to get fresh credentials")

class GoogleEventService:
    """Google Event service class"""

    @classmethod
    def list_events(cls, creds: Credentials, limit: Optional[int] = 10, start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None, order_by: Optional[Literal["startTime"]] = None) -> List[GoogleEvent]:
        """List events"""
        try:
            service = cls._build_service(creds)
            response = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_dt.astimezone(timezone.utc).isoformat() if start_dt else None,
                    timeMax=end_dt.astimezone(timezone.utc).isoformat() if end_dt else None,
                    maxResults=limit,
                    singleEvents=True,
                    orderBy = order_by #if time_range != "all" else None
                )
                .execute()
            )
            events = [
                GoogleEvent.model_validate(e)
                for e in response.get("items", [])
            ]
            return events
        except Exception:
            logger.exception("Failed to list events")
            raise InternalError("Failed to list events")        

    @classmethod
    def get_event(cls, creds: Credentials, event_id: str) -> GoogleEvent:
        """Get event by event ID"""
        try:
            service = cls._build_service(creds)
            event = service.events().get(calendarId="primary", eventId=event_id).execute()
            return GoogleEvent.model_validate(event)
        except Exception:
            logger.exception("Failed to get event")
            raise InternalError("Failed to get event")

    @classmethod
    def create_event(cls, creds: Credentials, payload: dict) -> GoogleEvent:
        """Create event from a dict payload"""
        try:
            service = cls._build_service(creds)
            body = {}
            if "title" in payload:
                body["summary"] = payload["title"]
            if "description" in payload:
                body["description"] = payload["description"]
            if "location" in payload:
                body["location"] = payload["location"]
            if "attendees" in payload:
                body["attendees"] = [{"email": e} for e in payload["attendees"]]
            if "start_dt" in payload and "end_dt" in payload:
                body["start"] = {
                    "dateTime": payload["start_dt"].astimezone(timezone.utc).isoformat(),
                    "timeZone": "UTC"
                }
                body["end"] = {
                    "dateTime": payload["end_dt"].astimezone(timezone.utc).isoformat(),
                    "timeZone": "UTC",
                }
            event = service.events().insert(calendarId="primary", body=body).execute()
            logger.warning(f" Event created: {event.get('htmlLink')}")
            return GoogleEvent.model_validate(event)
        except Exception:
            logger.exception("Failed to create event")
            raise InternalError("Failed to create event")            

    @classmethod
    def update_event(cls, creds: Credentials, event_id: str, payload: dict) -> GoogleEvent:
        """Update event using dict payload"""
        try:
            service = cls._build_service(creds)
            body = {}
            if "title" in payload:
                body["summary"] = payload["title"]
            if "description" in payload:
                body["description"] = payload["description"]
            if "location" in payload:
                body["location"] = payload["location"]
            if "attendees" in payload:
                body["attendees"] = [{"email": e} for e in payload["attendees"]]
            if "start_dt" in payload and "end_dt" in payload:
                body["start"] = {
                    "dateTime": payload["start_dt"].astimezone(timezone.utc).isoformat(),
                    "timeZone": "UTC"
                }
                body["end"] = {
                    "dateTime": payload["end_dt"].astimezone(timezone.utc).isoformat(),
                    "timeZone": "UTC",
                }
            event = service.events().patch(calendarId="primary", eventId=event_id, body=body).execute()
            return GoogleEvent.model_validate(event)
        except Exception:
            logger.exception("Failed to update event")
            raise InternalError("Failed to update event")

    @classmethod
    def delete_event(cls, creds: Credentials, event_id: str) -> bool:
        """Delete event by event ID"""
        try:
            service = cls._build_service(creds)
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            return True
        except Exception:
            logger.exception("Failed to delete event")
            raise InternalError("Failed to delete event")

    @classmethod
    def _build_service(cls, creds: Credentials) -> GoogleResource:
        """Build calendar service"""
        try:
            return build("calendar", "v3", credentials=creds)
        except Exception:
            logger.exception("Failed to build calendar service")
            raise InternalError("Failed to build calendar service")

    # @staticmethod
    # def _convert_to_google_datetime(dt: datetime) -> dict:
    #     try:
    #         return {
    #             "dateTime": dt.astimezone(timezone.utc).isoformat(),
    #             "timeZone": "UTC",
    #         }
    #     except Exception:
    #         logger.exception("Failed to convert datetime to Google datetime")
    #         raise InternalError("Failed to convert datetime to Google datetime")