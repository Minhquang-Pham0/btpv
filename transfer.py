from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from fastapi.security import OAuth2PasswordRequestForm
from ...core.exceptions import AuthenticationError
from ...services.auth_service import AuthService
from ...models.schemas.user import UserCreate, User
from ...models.schemas.token import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends()
) -> Any:
    """Register a new user."""
    try:
        return await auth_service.create_user(user_data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends()
) -> Any:
    """OAuth2 compatible token login."""
    try:
        user = await auth_service.authenticate_user(
            form_data.username,
            form_data.password
        )
        return auth_service.create_access_token({"sub": user.username})
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/test-token", response_model=User)
async def test_token(
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """Test access token."""
    return current_user
    
    
    from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes import auth, groups, passwords

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

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(groups.router, prefix=settings.API_V1_STR)
app.include_router(passwords.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    
    from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str
    
    