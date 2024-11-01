from .config import settings
from .security import (
    create_access_token,
    verify_password,
    get_password_hash,
    verify_access_token
)
from .exceptions import (
    PasswordVaultException,
    AuthenticationError,
    PermissionDenied,
    NotFoundError,
    ValidationError,
    DuplicateError
)

# Version
__version__ = "0.1.0"

__all__ = [
    "settings",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "verify_access_token",
    "PasswordVaultException",
    "AuthenticationError",
    "PermissionDenied",
    "NotFoundError",
    "ValidationError",
    "DuplicateError"
]