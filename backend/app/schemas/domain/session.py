from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


# Data Transfer Objects
class SessionDTO(BaseModel):
    """Base Data Transfer Object for Session entity."""
    id: UUID
    created_at: datetime
    updated_at: datetime    
    user_id: UUID
    provider_thread_id: str
    topic: Optional[str] = None    
    model_config = ConfigDict(from_attributes=True)

class SessionCreateDTO(BaseModel):
    """Data Transfer Object for creating a new Session."""
    user_id: UUID
    provider_thread_id: str
    topic: Optional[str] = None

