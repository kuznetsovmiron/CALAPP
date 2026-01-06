import logging
from datetime import timezone
from uuid import UUID

from app.orm.token import TokenOrm
from app.repository.token import TokenRepository
from app.schemas.domain.token import TokenProviderEnum
from app.services.system.exceptions import InternalError
from app.services.external.google import GoogleAuthService


logger = logging.getLogger(__name__)

class CalendarConnectionService:
    """Service class for managing calendar connection operations."""

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
            return url
        except Exception:
            logger.exception("Failed to request token from Google")
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
        except Exception:
            logger.exception(f"Failed to store token in the database")
            raise InternalError("Failed to store token in the database")
