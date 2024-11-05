# app/api/routes/passwords.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List
from ..services.password_service import PasswordService
from ..services.auth_service import AuthService
from ..core.security import oauth2_scheme
from ..models.schemas import Password, PasswordCreate, PasswordUpdate
from ..models.entities import User
from ..core.exceptions import NotFoundError, PermissionDenied

router = APIRouter(prefix="/passwords", tags=["passwords"])

async def get_current_user(
    auth_service: AuthService = Depends(),
    token: str = Depends(oauth2_scheme)
) -> User:
    return await auth_service.get_current_user(token)

@router.get("/group/{group_id}", response_model=List[Password])
async def get_group_passwords(
    group_id: int,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(get_current_user)
) -> List[Password]:
    """Get all passwords in a group."""
    try:
        if not group_id or not isinstance(group_id, int):
            raise HTTPException(
                status_code=422,
                detail="Invalid group ID provided"
            )
        
        return await password_service.get_group_passwords(group_id, current_user)
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# app/services/password_service.py
class PasswordService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        encryption: EncryptionService = Depends()
    ):
        self.db = db
        self.encryption = encryption

    async def get_group_passwords(self, group_id: int, user: User) -> List[Password]:
        """Get all passwords in a group"""
        # Verify user is member of the group
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundError("Group not found")
            
        if user not in group.members:
            raise PermissionDenied("You don't have access to this group")

        # Get passwords
        passwords = self.db.query(Password).filter(Password.group_id == group_id).all()
        
        # Return passwords without decrypted values
        return [
            Password(
                id=p.id,
                title=p.title,
                username=p.username,
                url=p.url,
                notes=p.notes,
                group_id=p.group_id,
                created_at=p.created_at,
                updated_at=p.updated_at
            ) for p in passwords
        ]