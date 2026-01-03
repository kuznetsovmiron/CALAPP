from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from typing_extensions import Literal


# Data Transfer Objects
class EventDTO(BaseModel):
    """Base Data Transfer Object for calendar."""
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    start_dt: datetime
    end_dt: datetime
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

# Commands (inputs / intents)
class EventListCommand(BaseModel):
    """Command for listing calendar events."""
    time_expression: Optional[str] = None
    duration_minutes: int = Field(default=60, ge=1)
    limit: int = Field(default=10, ge=1)

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def normalize_duration(cls, v):
        return 60 if v is None else v

    @field_validator("limit", mode="before")
    @classmethod
    def normalize_limit(cls, v):
        return 10 if v is None else v

class EventCreateCommand(BaseModel):
    """Command for creating a calendar event."""
    title: str
    time_expression: str
    duration_minutes: Optional[int] = Field(default=60, ge=1)
    description: Optional[str] = None    
    location: Optional[str] = None
    attendees: Optional[List[str]] = None    

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def set_default_duration(cls, v):
        return v or 60 

class EventUpdateCommand(BaseModel):
    """Command for updating a calendar event."""
    title: Optional[str] = None
    time_expression: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def normalize_duration(cls, v):
        return v  # keep None, let service decide