# app/services/user_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import Depends
from ..core.security import get_password_hash, verify_password
from ..models.entities import User
from ..models.schemas import UserCreate, UserUpdate
from ..core.exceptions import PermissionDenied, DuplicateError, NotFoundError
from ..db import get_db

class UserService:
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize UserService with database session"""
        self.db = db

    async def create_user(self, user_data: UserCreate, current_user: User) -> User:
        """
        Create a new user (admin only)
        
        Args:
            user_data: User creation data
            current_user: Currently authenticated user
            
        Returns:
            Created user instance
            
        Raises:
            PermissionDenied: If current user is not admin
            DuplicateError: If username or email already exists
        """
        if not current_user.is_admin:
            raise PermissionDenied("Only administrators can create users")

        # Check if user already exists
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise DuplicateError("Username already registered")
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise DuplicateError("Email already registered")

        # Create new user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            is_admin=user_data.is_admin if hasattr(user_data, 'is_admin') else False
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    async def get_users(self, current_user: User) -> List[User]:
        """
        Get all users (admin only)
        
        Args:
            current_user: Currently authenticated user
            
        Returns:
            List of all users
            
        Raises:
            PermissionDenied: If current user is not admin
        """
        if not current_user.is_admin:
            raise PermissionDenied("Only administrators can view user list")
            
        return self.db.query(User).all()

    async def get_user(self, user_id: int, current_user: User) -> User:
        """
        Get user by ID (admin or self)
        
        Args:
            user_id: ID of user to retrieve
            current_user: Currently authenticated user
            
        Returns:
            User instance
            
        Raises:
            NotFoundError: If user does not exist
            PermissionDenied: If current user is not admin and not requesting self
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
            
        if not current_user.is_admin and current_user.id != user_id:
            raise PermissionDenied("You can only view your own user details")
            
        return user

    async def update_password(
        self, 
        user_id: int, 
        current_password: str, 
        new_password: str, 
        current_user: User
    ) -> User:
        """
        Update user password (self only)
        
        Args:
            user_id: ID of user to update
            current_password: Current password for verification
            new_password: New password to set
            current_user: Currently authenticated user
            
        Returns:
            Updated user instance
            
        Raises:
            NotFoundError: If user does not exist
            PermissionDenied: If current user is not the target user or password is incorrect
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
            
        # Only allow users to change their own password
        if current_user.id != user_id:
            raise PermissionDenied("You can only change your own password")
            
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise PermissionDenied("Current password is incorrect")
            
        # Update password
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    async def update_user(self, user_id: int, user_data: UserUpdate, current_user: User) -> User:
        """
        Update user details (admin for all fields, self for limited fields)
        
        Args:
            user_id: ID of user to update
            user_data: Update data
            current_user: Currently authenticated user
            
        Returns:
            Updated user instance
            
        Raises:
            NotFoundError: If user does not exist
            PermissionDenied: If current user is not admin and not updating self
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")

        # Regular users can only update their own non-privileged fields
        if not current_user.is_admin:
            if current_user.id != user_id:
                raise PermissionDenied("You can only update your own user details")
            
            # Remove admin-only fields
            user_data_dict = user_data.dict(exclude_unset=True)
            allowed_fields = {'email'}  # Add other allowed fields here
            for field in list(user_data_dict.keys()):
                if field not in allowed_fields:
                    del user_data_dict[field]
        else:
            user_data_dict = user_data.dict(exclude_unset=True)

        # Update fields
        for field, value in user_data_dict.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int, current_user: User) -> None:
        """
        Delete user (admin only)
        
        Args:
            user_id: ID of user to delete
            current_user: Currently authenticated user
            
        Raises:
            NotFoundError: If user does not exist
            PermissionDenied: If current user is not admin
        """
        if not current_user.is_admin:
            raise PermissionDenied("Only administrators can delete users")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
            
        self.db.delete(user)
        self.db.commit()