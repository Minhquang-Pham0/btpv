from typing import List
from sqlalchemy.orm import Session
from fastapi import Depends
from app.models.entities import Password, User, Group
from app.models.schemas import PasswordCreate, PasswordUpdate
from app.core.exceptions import NotFoundError, PermissionDenied
from app.db import get_db
from .encryption_service import EncryptionService

class PasswordService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        encryption: EncryptionService = Depends()
    ):
        self.db = db
        self.encryption = encryption

    async def create_password(self, password_data: PasswordCreate, current_user: User) -> Password:
        """Create a new password entry"""
        # Verify user is member of the group
        group = await self._verify_group_access(password_data.group_id, current_user)
        
        # Encrypt the password
        encrypted_password = self.encryption.encrypt_password(password_data.password)
        
        password = Password(
            title=password_data.title,
            username=password_data.username,
            encrypted_password=encrypted_password,
            url=password_data.url,
            notes=password_data.notes,
            group_id=group.id
        )
        
        self.db.add(password)
        self.db.commit()
        self.db.refresh(password)
        return password

    async def get_password(self, password_id: int, current_user: User) -> Password:
        """Get a password entry with decrypted password"""
        password = self.db.query(Password).filter(Password.id == password_id).first()
        if not password:
            raise NotFoundError("Password not found")
            
        # Verify access
        await self._verify_group_access(password.group_id, current_user)
        
        # Create a copy with decrypted password
        password_copy = Password(
            id=password.id,
            title=password.title,
            username=password.username,
            encrypted_password=self.encryption.decrypt_password(password.encrypted_password),
            url=password.url,
            notes=password.notes,
            group_id=password.group_id
        )
        
        return password_copy

    async def update_password(
        self,
        password_id: int,
        password_data: PasswordUpdate,
        current_user: User
    ) -> Password:
        """Update a password entry"""
        password = self.db.query(Password).filter(Password.id == password_id).first()
        if not password:
            raise NotFoundError("Password not found")
            
        # Verify access
        await self._verify_group_access(password.group_id, current_user)
        
        # Update fields
        update_data = password_data.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["encrypted_password"] = self.encryption.encrypt_password(
                update_data.pop("password")
            )
            
        for field, value in update_data.items():
            setattr(password, field, value)
            
        self.db.commit()
        self.db.refresh(password)
        return password

    async def delete_password(self, password_id: int, current_user: User) -> None:
        """Delete a password entry"""
        password = self.db.query(Password).filter(Password.id == password_id).first()
        if not password:
            raise NotFoundError("Password not found")
            
        # Verify access
        await self._verify_group_access(password.group_id, current_user)
        
        self.db.delete(password)
        self.db.commit()

    async def get_group_passwords(self, group_id: int, current_user: User) -> List[Password]:
        """Get all passwords in a group"""
        # Verify access
        await self._verify_group_access(group_id, current_user)
        
        return self.db.query(Password).filter(Password.group_id == group_id).all()

    async def _verify_group_access(self, group_id: int, user: User) -> Group:
        """Verify user has access to the group"""
        # Check if user is a member of the group using a proper query
        group = (
            self.db.query(Group)
            .join(Group.members)
            .filter(
                Group.id == group_id,
                User.id == user.id
            )
            .first()
        )
        
        if not group:
            raise PermissionDenied("You don't have access to this group")
        
        return group