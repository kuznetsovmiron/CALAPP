from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


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
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    limit: int = Field(default=10, ge=1)

class EventCreateCommand(BaseModel):
    """Command for creating a calendar event."""
    title: str
    start_dt: datetime
    end_dt: datetime
    description: Optional[str] = None    
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

class EventUpdateCommand(BaseModel):
    """Command for updating a calendar event."""
    title: Optional[str] = None
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None