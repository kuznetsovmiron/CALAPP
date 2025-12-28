import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


# Nested Data Transfer Objects
class UserStateEnum(str, Enum):
    """Enumeration for user account states."""
    active = "active"
    disabled = "disabled"

# Data Transfer Objects
class UserDTO(BaseModel):
    """Base Data Transfer Object for User entity."""
    id: UUID
    created_at: datetime.datetime
    status: UserStateEnum
    email: EmailStr
    password: str
    name: str
    model_config = ConfigDict(from_attributes=True)

class UserExternalDTO(BaseModel):
    """External Data Transfer Object for User entity."""
    id: UUID
    created_at: datetime.datetime    
    status: UserStateEnum
    email: EmailStr
    name: str

class UserCreateDTO(BaseModel):
    """Data Transfer Object for creating a new user."""
    email: EmailStr
    password: str
    name: str

class UserUpdateDTO(BaseModel):
    """Data Transfer Object for updating user information."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class UserUpdatePasswordDTO(BaseModel):
    """Data Transfer Object for updating user password."""
    password: str