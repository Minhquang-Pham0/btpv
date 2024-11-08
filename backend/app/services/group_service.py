from typing import List
from sqlalchemy.orm import Session
from fastapi import Depends
from ..models.entities import Group, User, Password
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

    async def add_member(
        self,
        group_id: int,
        username: str,
        current_user: User
    ) -> Group:
        """Add a member to a group"""
        # Find the group
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundError("Group not found")

        # Check permissions
        if group.owner_id != current_user.id:
            raise PermissionDenied("Only the group owner can add members")

        # Find the user to add
        user_to_add = self.db.query(User).filter(User.username == username).first()
        if not user_to_add:
            raise NotFoundError(f"User {username} not found")

        # Add the user to the group if they're not already a member
        if user_to_add not in group.members:
            group.members.append(user_to_add)
            self.db.commit()
            self.db.refresh(group)

        return group

    async def remove_member(
        self, 
        group_id: int, 
        username: str, 
        current_user: User
    ) -> Group:
        """Remove a member from a group"""
        # Find the group
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundError("Group not found")

        # Check permissions
        if group.owner_id != current_user.id:
            raise PermissionDenied("Only the group owner can remove members")

        # Find the user to remove
        user_to_remove = self.db.query(User).filter(User.username == username).first()
        if not user_to_remove:
            raise NotFoundError(f"User {username} not found")

        # Can't remove the owner
        if user_to_remove.id == group.owner_id:
            raise PermissionDenied("Cannot remove the group owner")

        # Remove the user from the group
        if user_to_remove in group.members:
            group.members.remove(user_to_remove)
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
    

    async def delete_group(self, group_id: int, current_user: User) -> None:
        """Delete a group"""
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundError("Group not found")
            
        if group.owner_id != current_user.id:
            raise PermissionDenied("Only the group owner can delete the group")
        
        try:
            # Delete all associated passwords
            self.db.query(Password).filter(Password.group_id == group_id).delete()
            
            # Delete the group
            self.db.delete(group)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete group: {str(e)}")