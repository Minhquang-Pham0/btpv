from .auth import router as auth_router
from .groups import router as groups_router
from .passwords import router as passwords_router

__all__ = ["auth_router", "groups_router", "passwords_router"]