from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel


# Nested Data Transfer Objects
class GoogleEventDateTime(BaseModel):
    date: Optional[str] = None  # "YYYY-MM-DD"
    dateTime: Optional[datetime] = None  # ISO datetime
    timeZone: Optional[str] = "UTC"

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class GoogleEventAttendee(BaseModel):
    email: str
    displayName: Optional[str] = None
    responseStatus: Optional[str] = None    

# Base DTO
class GoogleEvent(BaseModel):
    id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    start: GoogleEventDateTime
    end: GoogleEventDateTime
    location: Optional[str] = None
    attendees: Optional[List[GoogleEventAttendee]] = None

class GoogleEventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start: GoogleEventDateTime
    end: GoogleEventDateTime
    location: Optional[str] = None
    attendees: Optional[List[GoogleEventAttendee]] = None

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }