from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
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
    time_expression: Optional[str] = None  # e.g., "next week", "tomorrow"
    duration_minutes: int = Field(default=60, ge=1)           # default window for the query    
    limit: int = 10                        # default limit for the query (max 50 events per query)
    time_range: Literal["past", "future", "all"] = "future"  # default time range for the query

class EventCreateCommand(BaseModel):
    """Command for creating a calendar event."""
    title: str
    time_expression: str
    duration_minutes: int = Field(default=60, ge=1)
    description: Optional[str] = None    
    location: Optional[str] = None
    attendees: Optional[List[str]] = None    

class EventUpdateCommand(BaseModel):
    """Command for updating a calendar event."""
    title: Optional[str] = None
    description: Optional[str] = None
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None