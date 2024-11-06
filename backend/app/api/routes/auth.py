# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
from ...core.exceptions import AuthenticationError
from ...services import AuthService
from ...models.schemas import Token, UserCreate, User

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
        token = auth_service.create_access_token(subject=user.username)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )