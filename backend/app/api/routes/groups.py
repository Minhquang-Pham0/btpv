# app/api/routes/groups.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List

from ...services.user_service import UserService
from ...services import GroupService
from ...services.auth_service import AuthService
from ...core.security import verify_access_token, oauth2_scheme
from ...models.schemas import Group, GroupCreate, GroupUpdate, User
from ...models.entities import User as UserModel
from ...db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/groups", tags=["groups"])

# Define get_current_user dependency
async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)

@router.post("/{group_id}/members/{username}", response_model=Group)
async def add_group_member(
    *,  # Force keyword arguments
    group_id: int,
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to the group"""
    group_service = GroupService(db)
    return await group_service.add_member(group_id, username, current_user)

@router.delete("/{group_id}/members/{username}", response_model=Group)
async def remove_group_member(
    *,  # Force keyword arguments
    group_id: int,
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from the group"""
    group_service = GroupService(db)
    return await group_service.remove_member(group_id, username, current_user)

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


@router.get("/{group_id}/available-users", response_model=List[User])
async def get_available_users(
    group_id: int,
    user_service: UserService = Depends(),
    current_user: User = Depends(get_current_user)
):
    """Get users that can be added to the group"""
    return await user_service.get_available_users(group_id, current_user)