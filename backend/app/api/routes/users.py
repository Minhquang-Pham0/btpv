# app/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ...services import UserService, AuthService
from ...models.schemas import (
    User, 
    UserCreate, 
    UserUpdate, 
    UserChangePassword
)
from ...core.security import oauth2_scheme
from ...core.exceptions import AuthenticationError
from ...db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=User)
async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Get current user details"""
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("", response_model=User)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Create new user (admin only)"""
    return await user_service.create_user(user_data, current_user)

@router.get("", response_model=List[User])
async def get_users(
    user_service: UserService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get all users (admin only)"""
    return await user_service.get_users(current_user)

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get user by ID (admin or self)"""
    return await user_service.get_user(user_id, current_user)

@router.post("/me/change-password", response_model=User)
async def change_password(
    password_data: UserChangePassword,
    user_service: UserService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Change current user password"""
    return await user_service.update_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password,
        current_user
    )


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Update user details (admin for all fields, self for limited fields)"""
    return await user_service.update_user(user_id, user_data, current_user)

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Delete user (admin only)"""
    await user_service.delete_user(user_id, current_user)
    return {"message": "User deleted successfully"}