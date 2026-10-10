from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, verify_password
from app.db.models import User
from app.schemas import LoginRequest, TokenResponse, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> User:
    return user

