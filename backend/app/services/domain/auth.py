import logging

from app.core.security import generate_token
from app.schemas.domain.auth import AuthLogin, AuthToken
from app.services.domain.user import UserService
from app.services.system.exceptions import UnauthorizedError, InternalError, NotFoundError


logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service class"""

    # Public API methods
    @classmethod
    async def login(cls, data: AuthLogin) -> AuthToken:
        """Public: Login user"""
        try:
            user = await UserService.retrieve_by_email(data.email)       
            if user.password != data.password:
                raise UnauthorizedError("Invalid credentials")            
            return AuthToken(
                user_id=user.id,
                token=generate_token(user.id)
            )
        except UnauthorizedError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.exception(f"LOGGER:Failed to login user with email={data.email}")
            raise InternalError("Failed to login")