# Add these imports at the beginning of config.py
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator
import secrets

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "Password Vault"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    POSTGRES_SERVER: str = "localhost"  # Add default
    POSTGRES_USER: str = "password_vault"  # Add default
    POSTGRES_PASSWORD: str = ""  # Will be set by environment
    POSTGRES_DB: str = "password_vault"  # Add default
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        
        # Ensure we have all required values
        user = values.get("POSTGRES_USER", "password_vault")
        password = values.get("POSTGRES_PASSWORD", "")
        server = values.get("POSTGRES_SERVER", "localhost")
        db = values.get("POSTGRES_DB", "password_vault")
        
        if not all([user, password, server, db]):
            raise ValueError("Missing database configuration values")
        
        return PostgresDsn.build(
            scheme="postgresql",
            username=user,
            password=password,
            host=server,
            path=f"/{db}",
        )

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()