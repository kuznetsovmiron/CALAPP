from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import RedirectResponse

from app.core.security import get_user_id
from app.services.domain.calendar import CalendarService
from app.services.system.exceptions import InternalError


router = APIRouter()

@router.get("/events", status_code=status.HTTP_200_OK)
async def list_events(user_id: UUID = Depends(get_user_id)):
    """List events for the current user."""
    try:
        return await CalendarService.list_events(user_id)
    except InternalError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
