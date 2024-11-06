# app/db/session.py
from typing import Generator
from sqlalchemy.orm import Session
from .base_class import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()