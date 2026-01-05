from typing import Callable, Dict, Optional
from uuid import UUID
from typing import List
from app.services.domain.event import EventService
from app.schemas.domain.event import EventCreateCommand, EventListCommand, EventUpdateCommand

# List of tools
async def registry_list_events(
    user_id: UUID,
    time_expression: str,
    duration_minutes: Optional[int] = None,
    limit: Optional[int] = None,    
) -> str:
    """Tool: list upcoming calendar events. Delegates logic to domain EventService."""
    command = EventListCommand(
        time_expression=time_expression,
        duration_minutes=duration_minutes,
        limit=limit
    )
    events = await EventService.list_events(user_id, command)
    return [
        {
            "id": e.id,
            "title": e.title,
            "start_dt": e.start_dt.isoformat(),
            "end_dt": e.end_dt.isoformat(),
            "description": e.description,
            "location": e.location,
            "attendees": e.attendees,
        }
        for e in events
    ]


async def registry_create_event(
    user_id: UUID,
    title: str,
    time_expression: str,
    duration_minutes: Optional[int] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
) -> str:
    """Tool: create a calendar event. Delegates logic to domain EventService."""
    command = EventCreateCommand(
        title=title,
        description=description,
        time_expression=time_expression,
        duration_minutes=duration_minutes,
        location=location,
        attendees=attendees,
    )
    event = await EventService.create_event(user_id, command)
    return f"Event created: {event.title} ({event.start_dt})"


async def registry_update_event(
    user_id: UUID,
    event_id: str,
    title: Optional[str] = None,
    time_expression: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
) -> str:
    """Tool: update a calendar event. Delegates logic to domain EventService."""
    command = EventUpdateCommand(
        title=title,
        time_expression=time_expression,
        duration_minutes=duration_minutes,
        location=location,
        description=description,
        attendees=attendees,
    )
    event = await EventService.update_event(user_id, event_id, command)
    return f"Event updated: {event.title} ({event.start_dt})"


async def registry_delete_event(
    user_id: UUID,
    event_id: str,
) -> str:
    """Tool: delete a calendar event. Delegates logic to domain EventService."""
    await EventService.delete_event(user_id, event_id)
    return f"Event deleted: {event_id}"


# Central registry of tool handlers
TOOL_REGISTRY: Dict[str, Callable] = {
    "create_event": registry_create_event,
    "list_events": registry_list_events,
    "update_event": registry_update_event,
    "delete_event": registry_delete_event,
}