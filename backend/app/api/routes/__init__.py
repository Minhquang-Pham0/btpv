from .auth import router as auth
from .groups import router as groups
from .passwords import router as passwords

__all__ = ["auth", "groups", "passwords"]