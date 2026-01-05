from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException

from app.core.security import get_user_id
from app.services.domain.event import EventService
from app.services.system.exceptions import InternalError


router = APIRouter()

@router.get("/events", status_code=status.HTTP_200_OK)
async def list_events(user_id: UUID = Depends(get_user_id)):
    """List events for the current user."""
    try:
        return await EventService.list_events(user_id)
    except InternalError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
