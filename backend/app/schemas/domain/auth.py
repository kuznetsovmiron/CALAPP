from uuid import UUID
from pydantic import BaseModel, EmailStr


# Data Transfer Objects
class AuthLogin(BaseModel):
    """User login credentials."""
    email: EmailStr
    password: str

class AuthToken(BaseModel):
    """Authentication token response."""
    user_id: UUID
    token: str