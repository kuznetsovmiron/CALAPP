from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Request, HTTPException, status
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS



def generate_token(user_id: UUID) -> str:
    """Generate a JWT token for a given user ID."""
    expire = datetime.now(timezone.utc) + timedelta(hours=int(ACCESS_TOKEN_EXPIRE_HOURS))
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return token


def check_access_token(request: Request) -> dict:
    """Validate and decode the JWT token from the request."""
    try:
        token = _get_token_from_request(request)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_user_id(request: Request) -> UUID:
    """Extract the user ID from the validated JWT token in the request."""
    payload = check_access_token(request)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")
    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID format in token")

def _get_token_from_request(request: Request) -> Optional[str]:
    """Extract the JWT token from the request's Authorization header or cookies."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    token = request.cookies.get("access_token")
    if token:
        return token
    return None