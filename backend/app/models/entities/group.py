from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ...db.base_class import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_groups")
    members = relationship(
        "User",
        secondary="group_members",
        back_populates="member_of_groups"
    )
    passwords = relationship("Password", back_populates="group")