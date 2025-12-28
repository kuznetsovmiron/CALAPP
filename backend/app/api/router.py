from fastapi import APIRouter, status

from app.api.system.handler import router as router_handler
from app.api.domain.auth import router as router_auth
from app.api.domain.profile import router as router_profile
from app.api.domain.calendar import router as router_calendar
from app.core.config import API_ROOT_PREFIX


# Main routing configuration
router_root: APIRouter = APIRouter(prefix=API_ROOT_PREFIX)
@router_root.get("/", status_code=status.HTTP_200_OK)
def get_root():
    return f"Welcome {API_ROOT_PREFIX}"

# Main routes
router_root.include_router(router_auth, prefix="/auth")
router_root.include_router(router_profile, prefix="/profile")
router_root.include_router(router_calendar, prefix="/calendar")

# System routes
router_root.include_router(router_handler, prefix="/handlers")
