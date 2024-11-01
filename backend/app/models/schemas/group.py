from pydantic import BaseModel
from typing import Optional, List
from .user import User

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Group(GroupBase):
    id: int
    owner_id: int
    owner: User
    members: List[User]
    
    class Config:
        from_attributes = True