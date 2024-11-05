from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List
from app.services import PasswordService, AuthService, EncryptionService
from app.models.schemas import Password, PasswordCreate, PasswordUpdate, User
from app.core.security import oauth2_scheme
from app.models.entities import User, Group
from app.core.exceptions import NotFoundError, PermissionDenied

router = APIRouter(prefix="/passwords", tags=["passwords"])

async def get_current_user(
    auth_service: AuthService = Depends(),
    token: str = Depends(oauth2_scheme)
) -> User:
    return await auth_service.get_current_user(token)

@router.get("/group/{group_id}", response_model=List[Password])
async def get_group_passwords(
    group_id: int,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(get_current_user)
) -> List[Password]:
    """Get all passwords in a group."""
    try:
        if not group_id or not isinstance(group_id, int):
            raise HTTPException(
                status_code=422,
                detail="Invalid group ID provided"
            )
        
        return await password_service.get_group_passwords(group_id, current_user)
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("", response_model=Password)
async def create_password(
    password_data: PasswordCreate,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create new password entry."""
    try:
        return await password_service.create_password(password_data, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

        
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

