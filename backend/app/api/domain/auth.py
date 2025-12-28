from fastapi import APIRouter, Response, status, HTTPException

from app.schemas.domain.auth import AuthLogin, AuthToken
from app.services.domain.auth import AuthService
from app.services.system.exceptions import InternalError, UnauthorizedError, NotFoundError


router = APIRouter()

@router.post("/login", status_code=status.HTTP_200_OK, response_model=AuthToken)
async def login(payload: AuthLogin, response: Response):
    """Authenticate user and return access token."""
    try:
        token_session = await AuthService.login(payload)
        response.set_cookie(
            key="access_token",
            value=token_session.token,
            httponly=True,
            secure=False,
            samesite="Lax"
        )
        return token_session
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    except InternalError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))    
