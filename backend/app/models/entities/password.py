from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ...db.base import Base

class Password(Base):
    __tablename__ = "passwords"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    username = Column(String)
    encrypted_password = Column(String)
    url = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="passwords")