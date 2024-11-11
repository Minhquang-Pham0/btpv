# app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..core import security, settings
from ..models.entities import User
from ..models.schemas import UserCreate, Token
from ..core.exceptions import AuthenticationError, DuplicateError
from ..db import get_db
from ..core.security import verify_access_token
from .log_service import LogService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

class AuthService:
    def __init__(self, db: Session = Depends(get_db), logging: LogService = Depends()):
        self.db = db
        self.logging = logging

    def create_access_token(self, subject: str) -> Token:
        """Create access token for given subject"""
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(
            subject=subject,
            expires_delta=expires_delta
        )
        return Token(access_token=token, token_type="bearer")

    async def get_current_user(self, token: str) -> User:
        """Get the current user from a JWT token"""
        try:
            username = verify_access_token(token)
            if not username:
                raise AuthenticationError("Invalid token")

            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                raise AuthenticationError("User not found")

            return user
        except Exception as e:
            raise AuthenticationError(str(e))


    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user and return the user object if successful"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        if not security.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")
            
        return user

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with encrypted password"""
        # Check if user already exists
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise DuplicateError("Username already registered")
        
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise DuplicateError("Email already registered")

        # Hash the password using bcrypt (for user authentication)
        hashed_password = security.get_password_hash(user_data.password)
        
        # Create new user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        log = await self.logging.create_log("Created User " + str(user.id))
        await self.logging.create_association(log, user.id, "user")

        return user

    @classmethod
    def get_current_user_dependency(cls):
        async def get_current_user(
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db)
        ) -> User:
            auth_service = cls(db)
            return await auth_service.get_current_user(token)
        return get_current_user