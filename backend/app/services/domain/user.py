import logging
from datetime import datetime, timezone
from uuid import UUID
from pydantic import EmailStr

from app.orm.user import UserOrm
from app.repository.user import UserRepository
from app.schemas.domain.user import UserDTO, UserCreateDTO, UserUpdateDTO, UserUpdatePasswordDTO
from app.services.system.exceptions import InternalError, NotFoundError, ForbiddenError


logger = logging.getLogger(__name__)

class UserService:
    """Service class for user operations."""

    # Public API methods
    @classmethod
    async def list(cls) -> list[UserDTO]:
        """Public: List users based on filters."""
        try:
            users = await UserRepository.list()
            if not users:
                return []
            return users
        except Exception:
            logger.exception(f"LOGGER:Failed to list users")
            raise InternalError("Failed to list users")

    @classmethod
    async def retrieve(cls, user_id: UUID) -> UserDTO: 
        """Public: Retrieve a user by ID."""
        try:
            user = await UserRepository.retrieve(user_id)
            if not user:
                raise NotFoundError("User not found")
            return user
        except NotFoundError:
            raise
        except Exception:
            logger.exception(f"LOGGER:Failed to retrieve user with user_id={user_id}")
            raise InternalError("Failed to retrieve user")

    @classmethod
    async def retrieve_by_email(cls, email: EmailStr) -> UserDTO:
        """Public: Retrieve a user by Email."""
        try:
            user = await UserRepository.retrieve_by_email(email)
            if not user:
                raise NotFoundError("User not found")
            if user.status == "disabled":
                raise ForbiddenError("User is disabled")
            return user
        except NotFoundError:
            raise
        except ForbiddenError:
            raise
        except Exception:
            logger.exception(f"LOGGER:Failed to retrieve user by email={email}")
            raise InternalError("Failed to retrieve user")

    @classmethod
    async def create(cls, data: UserCreateDTO) -> UserDTO:
        """Public: Create a new user."""
        try:             
            user_orm = UserOrm(**data.model_dump())
            return await UserRepository.create(user_orm)    
        except Exception:
            logger.exception(f"LOGGER:Failed to create user with data={data}")
            raise InternalError("Failed to create user")           

    @classmethod
    async def update(cls, user_id: UUID, data: UserUpdateDTO) -> UserDTO:
        """Public: Update an existing user."""
        try:   
            user = await UserRepository.retrieve(user_id)
            if not user:
                raise NotFoundError("User not found")
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(user, field, value)
            setattr(user, "updated_at", datetime.now(timezone.utc))
            return await UserRepository.update(user)
        except NotFoundError:
            raise
        except Exception:
            logger.exception(f"LOGGER:Failed to update user user_id={user_id}, data={data}")
            raise InternalError("Failed to update user")

    @classmethod
    async def update_password(cls, user_id: UUID, data: UserUpdatePasswordDTO) -> UserDTO:
        """Public: Update an existing user password."""
        try:
            user = await UserRepository.retrieve(user_id)
            setattr(user, "password", data.password)
            setattr(user, "updated_at", datetime.now(timezone.utc))
            return await UserRepository.update(user)
        except NotFoundError:
            raise
        except Exception:
            logger.exception(f"LOGGER:Failed to update user password for user_id={user_id}, data={data}")
            raise InternalError("Failed to update user password")