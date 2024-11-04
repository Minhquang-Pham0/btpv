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
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "password_vault"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "password_vault"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        
        # Get required values with error handling
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        server = values.get("POSTGRES_SERVER")
        db = values.get("POSTGRES_DB")

        # Validate all required values are present
        if not all([user, password, server, db]):
            missing = [
                key for key, value in {
                    "POSTGRES_USER": user,
                    "POSTGRES_PASSWORD": password,
                    "POSTGRES_SERVER": server,
                    "POSTGRES_DB": db
                }.items() if not value
            ]
            raise ValueError(f"Missing database configuration values: {', '.join(missing)}")

        # Build the database URL
        return f"postgresql://{user}:{password}@{server}/{db}"

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()