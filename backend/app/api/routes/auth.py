from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
from ....core.exceptions import AuthenticationError
from ....services import AuthService
from ....models.schemas import Token, UserCreate, User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends()
) -> Any:
    """Register a new user."""
    return await auth_service.create_user(user_data)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends()
) -> Any:
    """OAuth2 compatible token login."""
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        return {
            "access_token": auth_service.create_access_token(data={"sub": user.username}),
            "token_type": "bearer"
        }
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/test-token", response_model=User)
async def test_token(
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Test access token."""
    return current_user