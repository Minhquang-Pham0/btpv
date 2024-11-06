from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..core import security, settings
from ..models.entities import User
from ..models.schemas import UserCreate, Token
from ..core.exceptions import AuthenticationError, DuplicateError
from ..db import get_db
from .encryption_service import EncryptionService

# Configure OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

class AuthService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        encryption: EncryptionService = Depends()
    ):
        self.db = db
        self.encryption = encryption

    def create_access_token(self, subject: str) -> Token:
        """Create access token for given subject"""
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(
            subject=subject,
            expires_delta=expires_delta
        )
        return Token(access_token=token, token_type="bearer")

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
        return user

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """Get the current user from a JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Extract the raw token from the Bearer token
            if token.startswith('Bearer '):
                token = token[7:]
                
            username = security.verify_access_token(token)
            if not username:
                raise credentials_exception
                
            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                raise credentials_exception
                
            return user
            
        except Exception as e:
            raise credentials_exception