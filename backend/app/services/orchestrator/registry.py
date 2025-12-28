from typing import Callable, Dict, Literal, Optional
from uuid import UUID
from typing import List
from app.services.domain.calendar import CalendarService
from app.schemas.domain.calendar import EventCreateCommand, EventListCommand

# List of tools
async def registry_create_event(
    user_id: UUID,
    title: str,
    time_expression: str,
    duration_minutes: Optional[int] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
) -> str:
    """Tool: create a calendar event. Delegates logic to domain CalendarService."""
    command = EventCreateCommand(
        title=title,
        description=description,
        time_expression=time_expression,
        duration_minutes=duration_minutes,
        location=location,
        attendees=attendees,
    )
    event = await CalendarService.create_event(user_id, command)
    return f"Event created: {event.title} ({event.start_dt})"

async def registry_list_events(
    user_id: UUID,
    time_expression: str,
    duration_minutes: int,
    limit: int = 10,    
    time_range: Literal["past", "future", "all"] = "future",    
) -> str:
    """Tool: list upcoming calendar events. Delegates logic to domain CalendarService."""
    command = EventListCommand(
        time_expression=time_expression,
        duration_minutes=duration_minutes,
        limit=limit,
        time_range=time_range,
    )
    events = await CalendarService.list_events(user_id, command)
    return "\n".join(
        f"- {event.title} ({event.start_dt})"
        for event in events
    )

# Central registry of tool handlers
TOOL_REGISTRY: Dict[str, Callable] = {
    "create_event": registry_create_event,
    "list_events": registry_list_events,
}