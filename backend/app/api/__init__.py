from fastapi import APIRouter
from .routes import auth, groups, passwords

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(groups.router)
api_router.include_router(passwords.router)

__all__ = ["api_router"]