from fastapi import APIRouter, Depends
from typing import List
from app.services import AuthService, LogService
from app.models.entities import User
from app.models.schemas import Log
from app.core.security import oauth2_scheme

router = APIRouter(prefix="/logs", tags=["logs"])

async def get_current_user(
    auth_service: AuthService = Depends(),
    token: str = Depends(oauth2_scheme)
) -> User:
    return await auth_service.get_current_user(token)

@router.get("", response_model=List[Log])
async def get_logs(
    log_service: LogService = Depends(),
    current_user: User = Depends(get_current_user)
):
    return await log_service.get_logs(current_user)

@router.get("/{association_type}/{association_id}", response_model=List[Log])
async def get_logs_by(
    association_type: str,
    association_id: int,
    log_service: LogService = Depends(),
    current_user: User = Depends(get_current_user)
):
    return await log_service.get_logs_by(current_user, association_id, association_type)