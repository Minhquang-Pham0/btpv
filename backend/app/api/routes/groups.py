from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List
from app.services import GroupService
from app.services.auth_service import AuthService
from app.core.security import verify_access_token, oauth2_scheme
from app.models.schemas import Group, GroupCreate, GroupUpdate, User
from app.models.entities import User as UserModel

router = APIRouter(prefix="/groups", tags=["groups"])

async def get_current_user(
    auth_service: AuthService = Depends(),
    token: str = Depends(oauth2_scheme)
) -> UserModel:
    return await auth_service.get_current_user(token)

@router.post("", response_model=Group)
async def create_group(
    group_data: GroupCreate,
    group_service: GroupService = Depends(),
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """Create new group."""
    try:
        return await group_service.create_group(group_data, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[Group])
async def get_user_groups(
    group_service: GroupService = Depends(),
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """Get all groups user is member of."""
    try:
        return await group_service.get_user_groups(current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{group_id}", response_model=Group)
async def get_group(
    group_id: int,
    group_service: GroupService = Depends(),
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """Get a specific group."""
    try:
        return await group_service.get_group(group_id, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{group_id}", response_model=Group)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    group_service: GroupService = Depends(),
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """Update a group."""
    try:
        return await group_service.update_group(group_id, group_data, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{group_id}/members/{username}")
async def add_group_member(
    group_id: int,
    username: str,
    group_service: GroupService = Depends(),
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """Add a member to the group."""
    try:
        return await group_service.add_member(group_id, username, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{group_id}/members/{username}")
async def remove_group_member(
    group_id: int,
    username: str,
    group_service: GroupService = Depends(),
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """Remove a member from the group."""
    try:
        return await group_service.remove_member(group_id, username, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))