from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ...db.base_class import Base

class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime(timezone=True), server_default=func.now())
    msg = Column(String)

    associations = relationship("LogAssociation", back_populates="log")

class LogAssociation(Base):
    __tablename__ = 'log_associations'

    log_id = Column(Integer, ForeignKey('logs.id'), primary_key=True)
    association_id = Column(Integer, primary_key=True)
    association_type = Column(String, primary_key=True)

    log = relationship("Log", back_populates="associations")