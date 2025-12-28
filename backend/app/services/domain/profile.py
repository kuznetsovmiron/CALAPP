import logging
from uuid import UUID

from app.schemas.domain.profile import ProfileDTO, ProfileUpdateDTO, ProfileUpdatePasswordDTO
from app.schemas.domain.user import UserDTO, UserUpdatePasswordDTO
from app.services.domain.user import UserService
from app.services.system.exceptions import InternalError, NotFoundError, BadRequestError


logger = logging.getLogger(__name__)

class ProfileService:
    """Service class for managing profile operations."""

    # Public API methods
    @classmethod
    async def retrieve(cls, user_id: UUID) -> ProfileDTO:
        """Public: Retrieve full profile data with calculated attributes."""
        try:
            user = await UserService.retrieve(user_id)
            if not user:
                raise NotFoundError("User not found")
            return await cls._to_extended_dto(user)
        except NotFoundError:
            raise        
        except Exception as e:
            logger.exception(f"Failed to retrieve profile for user_id={user_id}: {e}", exc_info=e)
            raise InternalError("Failed to retrieve profile")
    
    @classmethod    
    async def update(cls, user_id: UUID, data: ProfileUpdateDTO) -> ProfileDTO:
        """Public: Update current user's profile data and return it with extended information."""
        try:
            user = await UserService.update(user_id, data)
            if not user:
                raise NotFoundError("User not found")
            return await cls._to_extended_dto(user)
        except NotFoundError:
            raise        
        except Exception as e:
            logger.exception(f"Failed to update profile for user_id={user_id}, data={data}: {e}", exc_info=e)
            raise InternalError("Failed to update profile")

    @classmethod
    async def update_password(cls, user_id: UUID, data: ProfileUpdatePasswordDTO) -> ProfileDTO:
        """Public: Update user's password."""
        try:
            user = await UserService.retrieve(user_id)
            if user.password != data.current_password:
                raise BadRequestError("Invalid credentials")
            user_update_dto = UserUpdatePasswordDTO(password=data.new_password)
            await UserService.update_password(user_id, user_update_dto)
        except BadRequestError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Failed to update password for user_id={user_id}: {e}", exc_info=e)
            raise InternalError("Failed to update password")

    # Private implementation methods
    @staticmethod
    async def _to_extended_dto(user: UserDTO) -> ProfileDTO:
        """Private: Convert ORM user to ProfileDTO"""
        return ProfileDTO(
            **UserDTO.model_validate(user).model_dump()
            ) 