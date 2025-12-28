import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict

from app.schemas.domain.user import UserStateEnum

# Data Transfer Objects
class ProfileDTO(BaseModel):
    """Base Data Transfer Object for user profile with subscription information."""
    id: UUID
    created_at: datetime.datetime    
    status: UserStateEnum
    email: EmailStr
    name: str
    model_config = ConfigDict(from_attributes=True)

class ProfileExternalDTO(ProfileDTO):
    """External Data Transfer Object for user profile with subscription information."""
    pass

class ProfileUpdateDTO(BaseModel):
    """Data Transfer Object for updating user profile information."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class ProfileUpdatePasswordDTO(BaseModel):
    """Data Transfer Object for updating user password."""
    current_password: str
    new_password: str