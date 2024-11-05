from typing import List
from sqlalchemy.orm import Session
from fastapi import Depends
from ..models.entities import Group, User
from ..models.schemas import GroupCreate, GroupUpdate
from ..core.exceptions import NotFoundError, PermissionDenied
from ..db import get_db

class GroupService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def create_group(self, group_data: GroupCreate, user: User) -> Group:
        """Create a new group"""
        group = Group(
            name=group_data.name,
            description=group_data.description,
            owner_id=user.id
        )
        group.members.append(user)  # Owner is automatically a member
        
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    async def get_group(self, group_id: int, user: User) -> Group:
        """Get a group if the user is a member"""
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundError("Group not found")
        if user not in group.members:
            raise PermissionDenied("You are not a member of this group")
        return group

    async def add_member(self, group_id: int, username: str, current_user: User) -> Group:
        """Add a member to a group"""
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundError("Group not found")
        if group.owner_id != current_user.id:
            raise PermissionDenied("Only the group owner can add members")

        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise NotFoundError("User not found")

        if user not in group.members:
            group.members.append(user)
            self.db.commit()
            self.db.refresh(group)

        return group

    async def remove_member(self, group_id: int, username: str, current_user: User) -> Group:
        """Remove a member from a group"""
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundError("Group not found")
        if group.owner_id != current_user.id:
            raise PermissionDenied("Only the group owner can remove members")

        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise NotFoundError("User not found")

        if user == current_user:
            raise PermissionDenied("Cannot remove the group owner")

        if user in group.members:
            group.members.remove(user)
            self.db.commit()
            self.db.refresh(group)

        return group

    async def get_user_groups(self, user: User) -> List[Group]:
        """Get all groups a user is a member of"""
        return self.db.query(Group).filter(
            (Group.owner_id == user.id) | (Group.members.any(id=user.id))
        ).all()

    async def update_group(self, group_id: int, group_data: GroupUpdate, current_user: User) -> Group:
        """Update a group's details"""
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundError("Group not found")
        if group.owner_id != current_user.id:
            raise PermissionDenied("Only the group owner can update the group")

        for field, value in group_data.dict(exclude_unset=True).items():
            setattr(group, field, value)

        self.db.commit()
        self.db.refresh(group)
        return group