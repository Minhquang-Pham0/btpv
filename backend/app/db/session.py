from typing import Generator
from .base import SessionLocal

def get_db() -> Generator:
    """
    Get database session.
    This should be used as a FastAPI dependency.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()