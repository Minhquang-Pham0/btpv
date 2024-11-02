from fastapi import APIRouter, Depends
from typing import Any, List
from app.services import GroupService, AuthService
from app.models.schemas import Group, GroupCreate, GroupUpdate, User

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("", response_model=Group)
async def create_group(
    group_data: GroupCreate,
    group_service: GroupService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Create new group."""
    return await group_service.create_group(group_data, current_user)

@router.get("", response_model=List[Group])
async def get_user_groups(
    group_service: GroupService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Get all groups user is member of."""
    return await group_service.get_user_groups(current_user)

@router.get("/{group_id}", response_model=Group)
async def get_group(
    group_id: int,
    group_service: GroupService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Get a specific group."""
    return await group_service.get_group(group_id, current_user)

@router.put("/{group_id}", response_model=Group)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    group_service: GroupService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Update a group."""
    return await group_service.update_group(group_id, group_data, current_user)

@router.post("/{group_id}/members/{username}")
async def add_group_member(
    group_id: int,
    username: str,
    group_service: GroupService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Add a member to the group."""
    return await group_service.add_member(group_id, username, current_user)

@router.delete("/{group_id}/members/{username}")
async def remove_group_member(
    group_id: int,
    username: str,
    group_service: GroupService = Depends(),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Remove a member from the group."""
    return await group_service.remove_member(group_id, username, current_user)