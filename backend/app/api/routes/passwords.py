from fastapi import APIRouter, Depends
from typing import Any, List
from app.services import PasswordService, AuthService, EncryptionService
from app.models.schemas import Password, PasswordCreate, PasswordUpdate, User

router = APIRouter(prefix="/passwords", tags=["passwords"])

@router.post("", response_model=Password)
async def create_password(
    password_data: PasswordCreate,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Create new password entry."""
    return await password_service.create_password(password_data, current_user)

@router.get("/group/{group_id}", response_model=List[Password])
async def get_group_passwords(
    group_id: int,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Get all passwords in a group."""
    return await password_service.get_group_passwords(group_id, current_user)

@router.get("/{password_id}", response_model=Password)
async def get_password(
    password_id: int,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Get a specific password entry."""
    return await password_service.get_password(password_id, current_user)

@router.put("/{password_id}", response_model=Password)
async def update_password(
    password_id: int,
    password_data: PasswordUpdate,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Update a password entry."""
    return await password_service.update_password(
        password_id,
        password_data,
        current_user
    )

@router.delete("/{password_id}")
async def delete_password(
    password_id: int,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Delete a password entry."""
    return await password_service.delete_password(password_id, current_user)

@router.post("/generate")
async def generate_password(
    length: int = 16,
    encryption_service: EncryptionService = Depends()
) -> Any:
    """Generate a random secure password."""
    return {"password": encryption_service.generate_password(length)}