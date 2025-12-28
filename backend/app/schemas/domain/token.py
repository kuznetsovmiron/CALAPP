import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


# Nested Data Transfer Objects
class TokenProviderEnum(str, Enum):
    """Enumeration for token providers."""
    google = "google"

# Data Transfer Objects
class TokenDTO(BaseModel):
    """Base Data Transfer Object for Token entity."""
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    provider: str
    access_token: str
    refresh_token: str
    expiry: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class TokenCreateDTO(BaseModel):
    """Data Transfer Object for creating a new token."""
    provider: TokenProviderEnum
    access_token: str
    refresh_token: str
    expiry: datetime.datetime

class TokenUpdateDTO(BaseModel):
    """Data Transfer Object for updating a token."""
    provider: Optional[TokenProviderEnum] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expiry: Optional[datetime.datetime] = None