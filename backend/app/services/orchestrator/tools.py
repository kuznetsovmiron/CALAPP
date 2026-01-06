import logging
from uuid import UUID
from typing import Any, Callable, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta
import parsedatetime

from app.services.domain.event import EventService
from app.schemas.domain.event import EventCreateCommand, EventListCommand, EventUpdateCommand
from app.services.system.exceptions import InternalError, ToolExecutionError
from app.schemas.orchestrator.tool import ToolCall

logger = logging.getLogger(__name__)

# -----------------------------
# Helper for parsing time expressions
# -----------------------------
def parse_time_expression(time_expression: str, duration_minutes: int, user_timezone: str = "Europe/Moscow") -> Tuple[datetime, datetime]:
    """Resolve a human-readable time expression into start_dt and end_dt (UTC)."""
    try:
        cal = parsedatetime.Calendar()
        parsed_time, status = cal.parseDT(
            time_expression,
            sourceTime=datetime.now(ZoneInfo(user_timezone))
            # sourceTime=datetime.now(timezone.utc).astimezone(ZoneInfo(user_timezone))
        )
        if status == 0 or parsed_time is None:
            raise ValueError("Could not parse time expression")
        start_dt = parsed_time.astimezone(timezone.utc)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        logger.warning(f" Parsed time expression UTC: {start_dt} - {end_dt} ")
        return start_dt, end_dt
    except Exception:
        raise InternalError(f"Failed to parse time expression: {time_expression}")

# -----------------------------
# Tool handlers (formerly registry)
# -----------------------------

async def list_events(user_id: UUID, time_expression: str, duration_minutes: Optional[int] = 60, limit: Optional[int] = 10) -> list[dict]:
    start_dt, end_dt = parse_time_expression(time_expression, duration_minutes or 60)
    command = EventListCommand(
        start_dt=start_dt,
        end_dt=end_dt,
        limit=limit or 10,
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

async def create_event(
    user_id: UUID,
    title: str,
    time_expression: str,
    duration_minutes: Optional[int] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
) -> str:
    start_dt, end_dt = parse_time_expression(time_expression, duration_minutes or 60)
    command = EventCreateCommand(
        title=title,
        start_dt=start_dt,
        end_dt=end_dt,
        description=description,
        location=location,
        attendees=attendees,
    )
    event = await EventService.create_event(user_id, command)
    return f"Event created: {event.title} ({event.start_dt.isoformat()})"

async def update_event(
    user_id: UUID,
    event_id: str,
    title: Optional[str] = None,
    time_expression: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
) -> str:
    start_dt = end_dt = None
    if time_expression:
        if duration_minutes is None:
            existing = await EventService.get_event(user_id, event_id)
            duration_minutes = int(
                (existing.end_dt - existing.start_dt).total_seconds() / 60
            )
        start_dt, end_dt = parse_time_expression(time_expression, duration_minutes)
    command = EventUpdateCommand(
        title=title,
        start_dt=start_dt,
        end_dt=end_dt,
        location=location,
        description=description,
        attendees=attendees,
    )
    event = await EventService.update_event(user_id, event_id, command)
    return f"Event updated: {event.title} ({event.start_dt.isoformat()})"

async def delete_event(user_id: UUID, event_id: str) -> str:
    await EventService.delete_event(user_id, event_id)
    return f"Event deleted: {event_id}"

# -----------------------------
# Central registry
# -----------------------------
TOOL_REGISTRY: Dict[str, Callable] = {
    "create_event": create_event,
    "list_events": list_events,
    "update_event": update_event,
    "delete_event": delete_event,
}

# -----------------------------
# Dispatcher (merged)
# -----------------------------
class ToolDispatcher:
    """Dispatches tool calls to the correct handler."""

    @classmethod
    async def dispatch(cls, user_id: UUID, tool_call: ToolCall) -> Any:
        try:
            handler = TOOL_REGISTRY.get(tool_call.name)
            if not handler:
                raise ToolExecutionError(f"Unknown tool: {tool_call.name}")
            return await handler(user_id=user_id, **tool_call.arguments)
        except ToolExecutionError:
            raise
        except Exception:
            logger.exception(f"LOGGER: Failed to execute tool '{tool_call.name}' for user {user_id}")
            raise ToolExecutionError(f"Failed to execute tool '{tool_call.name}' for user {user_id}")