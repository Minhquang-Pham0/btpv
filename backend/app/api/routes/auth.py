from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from fastapi.security import OAuth2PasswordRequestForm
from ...core.exceptions import AuthenticationError
from ...services.auth_service import AuthService
from ...models.schemas.user import UserCreate, User
from ...models.schemas.token import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends()
) -> Any:
    """Register a new user."""
    try:
        return await auth_service.create_user(user_data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends()
) -> Any:
    """OAuth2 compatible token login."""
    try:
        user = await auth_service.authenticate_user(
            form_data.username,
            form_data.password
        )
        return auth_service.create_access_token({"sub": user.username})
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/test-token", response_model=User)
async def test_token(
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Test access token."""
    return current_user