from fastapi import APIRouter, Request, status, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from uuid import UUID

from app.services.domain.calendar import CalendarService
from app.services.system.exceptions import InternalError
from app.core.security import get_user_id

router = APIRouter()

@router.get("/request", status_code=status.HTTP_302_FOUND)
async def request_token(user_id: UUID = Depends(get_user_id)):
    """Request token from Google."""
    try:
        url = await CalendarService.request_token(user_id)
        # return RedirectResponse(url)
        return {"url": url}
    except InternalError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))    


@router.get("/callback", status_code=status.HTTP_200_OK)
async def fetch_token(request: Request, state: str = Query(...)): # type: ignore
    """Fetch token from Google."""
    try:
        await CalendarService.fetch_token(request.url, state) 
        return {"status": "success"}
    except InternalError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))    
