from fastapi import APIRouter
from .routes import auth_router, groups_router, passwords_router, users_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(groups_router)
api_router.include_router(passwords_router)
api_router.include_router(users_router)

__all__ = ["api_router"]