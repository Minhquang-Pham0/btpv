from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends
from ..core import security, settings
from ..models.entities import User
from ..models.schemas import UserCreate
from ..core.exceptions import AuthenticationError, DuplicateError
from ..db import get_db

class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user and return the user object if successful"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not security.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")
        return user

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise DuplicateError("Username already registered")
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise DuplicateError("Email already registered")

        # Create new user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=security.get_password_hash(user_data.password)
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    async def get_current_user(self, token: str) -> User:
        """Get the current user from a JWT token"""
        username = security.verify_access_token(token)
        if not username:
            raise AuthenticationError()
            
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise AuthenticationError()
            
        return user