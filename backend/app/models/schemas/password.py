from pydantic import BaseModel, AnyUrl
from typing import Optional
from datetime import datetime

class PasswordBase(BaseModel):
    title: str
    username: str
    url: Optional[AnyUrl] = None
    notes: Optional[str] = None

class PasswordCreate(PasswordBase):
    password: str  # client-encrypted password
    encryption_key: str  # Client-generated encryption key
    group_id: int

class PasswordUpdate(BaseModel):
    title: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Client-encrypted password
    encryption_key: Optional[str] = None  # New encryption key if password is changed
    url: Optional[AnyUrl] = None
    notes: Optional[str] = None

class Password(PasswordBase):
    id: int
    group_id: int
    encrypted_password: str
    encryption_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    

class PasswordInDB(Password):
    encrypted_password: str