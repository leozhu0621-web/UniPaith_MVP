from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.database import get_db
from unipaith.dependencies import get_current_user, user_is_owner
from unipaith.models.user import User
from unipaith.schemas.auth import (
    GoogleCallbackRequest,
    GoogleSignInRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserResponse,
)
from unipaith.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.signup(body.email, body.password, body.role)
    return result


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.login(body.email, body.password)
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.refresh_token(body.refresh_token)
    return result


@router.post("/google-callback", response_model=LoginResponse)
async def google_callback(body: GoogleCallbackRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.google_callback(body.code, body.redirect_uri, body.role)
    return result


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        created_at=user.created_at,
        is_owner=user_is_owner(user),
        uni_guided=settings.ai_uni_guided_v1,
    )


@router.post("/google", response_model=LoginResponse)
async def google_signin(body: GoogleSignInRequest, db: AsyncSession = Depends(get_db)):
    """GIS-direct Google sign-in (demo). Verifies the Google ID token and
    returns the app session. Requires GOOGLE_CLIENT_ID configured."""
    svc = AuthService(db)
    return await svc.google_signin(body.id_token, body.role)
