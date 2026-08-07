"""API routers package."""

from app.api.auth import router as auth_router
from app.api.jobs import router as jobs_router
from app.api.matching import router as matching_router
from app.api.user_details import router as user_details_router

__all__ = ["auth_router", "jobs_router", "matching_router", "user_details_router"]
