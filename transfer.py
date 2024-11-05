from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes import auth, users, groups, passwords

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include routers with the API prefix
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(groups.router, prefix=settings.API_V1_STR)
app.include_router(passwords.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    
    from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List
from ..services.password_service import PasswordService
from ..services.auth_service import AuthService
from ..core.security import oauth2_scheme
from ..models.schemas import Password, PasswordCreate, PasswordUpdate
from ..models.entities import User

# Remove /api/v1 from the prefix as it's already included in main.py
router = APIRouter(prefix="/passwords", tags=["passwords"])

async def get_current_user(
    auth_service: AuthService = Depends(),
    token: str = Depends(oauth2_scheme)
) -> User:
    return await auth_service.get_current_user(token)

@router.post("", response_model=Password)
async def create_password(
    password_data: PasswordCreate,
    password_service: PasswordService = Depends(),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create new password entry."""
    try:
        return await password_service.create_password(password_data, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ... rest of the router code remains the same ...


from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List
from ..services import GroupService
from ..services.auth_service import AuthService
from ..core.security import verify_access_token, oauth2_scheme
from ..models.schemas import Group, GroupCreate, GroupUpdate, User
from ..models.entities import User as UserModel

# Remove /api/v1 from the prefix
router = APIRouter(prefix="/groups", tags=["groups"])

async def get_current_user(
    auth_service: AuthService = Depends(),
    token: str = Depends(oauth2_scheme)
) -> UserModel:
    return await auth_service.get_current_user(token)

@router.post("", response_model=Group)
async def create_group(
    group_data: GroupCreate,
    group_service: GroupService = Depends(),
    current_user: UserModel = Depends(get_current_user)
) -> Any:
    """Create new group."""
    try:
        return await group_service.create_group(group_data, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ... rest of the router code remains the same ...


    
    
    