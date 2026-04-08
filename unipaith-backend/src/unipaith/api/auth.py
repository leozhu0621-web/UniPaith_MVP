from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import get_current_user
from unipaith.models.user import User
from unipaith.schemas.auth import (
    GoogleCallbackRequest,
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
    )
