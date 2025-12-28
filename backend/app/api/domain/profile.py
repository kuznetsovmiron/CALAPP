from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_user_id
from app.schemas.domain.profile import ProfileUpdateDTO, ProfileExternalDTO, ProfileUpdatePasswordDTO
from app.services.domain.profile import ProfileService
from app.services.system.exceptions import InternalError, NotFoundError, BadRequestError


router = APIRouter()

@router.get("/", status_code=status.HTTP_200_OK, response_model=ProfileExternalDTO)
async def retrieve(user_id: UUID = Depends(get_user_id)):
    """Retrieve the current user's profile."""
    try:
        return await ProfileService.retrieve(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InternalError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.patch("/", status_code=status.HTTP_200_OK, response_model=ProfileExternalDTO)
async def update(data: ProfileUpdateDTO, user_id: UUID = Depends(get_user_id)):
    """Update current user's profile data."""
    try:
        return await ProfileService.update(user_id=user_id, data=data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InternalError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/password", status_code=status.HTTP_200_OK, response_model=None)
async def change_password(data: ProfileUpdatePasswordDTO, user_id: UUID = Depends(get_user_id)):
    """Change current user's password."""
    try:
        await ProfileService.update_password(user_id=user_id, data=data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InternalError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))