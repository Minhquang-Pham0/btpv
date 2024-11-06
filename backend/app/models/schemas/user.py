# app/models/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class UserChangePassword(BaseModel):
    current_password: str
    new_password: str

class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True

class User(UserBase):
    id: int

    class Config:
        from_attributes = True