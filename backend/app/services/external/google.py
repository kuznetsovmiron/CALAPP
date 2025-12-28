import logging
from typing import Dict, List, Tuple, Literal, Optional
import httplib2
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource as GoogleResource
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from app.schemas.external.google import GoogleEvent, GoogleEventCreate
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
        except Exception as e:
            logger.error(f"Error getting flow: {e}")
            raise InternalError("Failed to get flow")

    @classmethod
    def get_fresh_creds(cls, token: TokenOrm) -> Credentials:
        """Return credentials refreshed if expired and update DB if needed."""
        try:
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
        except RefreshError as e:
            raise InternalError("Google authorization expired. Please reconnect your calendar.")
        except Exception as e:
            logger.error(f"Error getting fresh credentials: {e}")
            raise InternalError(f"Failed to get fresh credentials: {e}")

class GoogleCalService:
    """Google Calendar service class"""

    @classmethod
    def list_events(
        cls,
        creds: Credentials,
        limit: Optional[int] = 10,
        start_dt: Optional[datetime] = None,
        end_dt: Optional[datetime] = None,
        order_by: Optional[Literal["startTime"]] = None,
    ) -> List[GoogleEvent]:
        """List events"""
        try:
            service = cls._build_service(creds)
            response = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_dt.isoformat() if start_dt else None,
                    timeMax=end_dt.isoformat() if end_dt else None,
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
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            raise InternalError("Failed to list events")        

    @classmethod
    def create_event(cls, creds: Credentials, body: GoogleEventCreate) -> GoogleEvent:
        """Create event"""
        try:
            service = cls._build_service(creds)
            event = service.events().insert(calendarId="primary", body=body.model_dump(mode="json", exclude_none=True)).execute()
            print(f"Event created: {event.get('htmlLink')}")
            return GoogleEvent.model_validate(event)
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise InternalError("Failed to create event")

    @classmethod
    def delete_event(cls, token: TokenOrm, event_id: str) -> bool:
        """Delete event"""
        try:
            service = cls._build_service(token)
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            raise InternalError("Failed to delete event")

    @classmethod
    def update_event(cls, token: TokenOrm, event_id: str, event: Dict) -> Dict:
        """Update event"""
        try:
            service = cls._build_service(token)
            event = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
            return event
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            raise InternalError("Failed to update event")

    @classmethod
    def _build_service(cls, creds: Credentials) -> GoogleResource:
        """Build calendar service"""
        try:
            return build("calendar", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Error building calendar service: {e}")
            raise InternalError("Failed to build calendar service")