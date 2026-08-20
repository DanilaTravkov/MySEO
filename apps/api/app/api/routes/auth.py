from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal, NamedTuple

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import (
    hash_password,
    hash_session_token,
    new_session_token,
    verify_password,
)
from app.db.session import get_session
from app.models.auth import User, UserSession

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) > 320 or "@" not in normalized:
        raise ValueError("Enter a valid email address.")
    local, _, domain = normalized.partition("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("Enter a valid email address.")
    return normalized


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str
    password: str = Field(min_length=8, max_length=128)
    company: str = Field(default="", max_length=160)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    remember: bool = False

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    email: str | None = None
    company: str | None = Field(default=None, max_length=160)
    role: str | None = Field(default=None, max_length=160)
    experience_level: Literal["guided", "advanced"] | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_email(value) if value is not None else None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str
    company: str
    role: str
    experience_level: str
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            company=user.company,
            role=user.role,
            experience_level=user.experience_level,
            created_at=user.created_at,
        )


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    expires_at: datetime


class AuthContext(NamedTuple):
    user: User
    auth_session: UserSession


def _session_expiry(settings: Settings, *, remember: bool) -> datetime:
    duration = (
        timedelta(days=settings.auth_remember_days)
        if remember
        else timedelta(hours=settings.auth_session_hours)
    )
    return datetime.now(UTC) + duration


def _create_session(
    database: Session,
    user: User,
    settings: Settings,
    *,
    remember: bool,
) -> tuple[str, UserSession]:
    token = new_session_token()
    auth_session = UserSession(
        user=user,
        token_hash=hash_session_token(token),
        expires_at=_session_expiry(settings, remember=remember),
    )
    database.add(auth_session)
    database.commit()
    database.refresh(auth_session)
    return token, auth_session


def get_auth_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    database: Annotated[Session, Depends(get_session)],
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    auth_session = database.scalar(
        select(UserSession).where(
            UserSession.token_hash == hash_session_token(credentials.credentials)
        )
    )
    if auth_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        database.delete(auth_session)
        database.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired.")
    return AuthContext(auth_session.user, auth_session)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    database: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email,
        company=payload.company.strip(),
        role="",
        experience_level="guided",
        password_hash=hash_password(payload.password),
    )
    database.add(user)
    try:
        database.flush()
    except IntegrityError as exc:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc
    token, auth_session = _create_session(database, user, settings, remember=True)
    return AuthResponse(
        user=UserResponse.from_user(user),
        access_token=token,
        expires_at=auth_session.expires_at,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    database: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    user = database.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        )
    token, auth_session = _create_session(database, user, settings, remember=payload.remember)
    return AuthResponse(
        user=UserResponse.from_user(user),
        access_token=token,
        expires_at=auth_session.expires_at,
    )


@router.get("/me", response_model=UserResponse)
def current_user(context: Annotated[AuthContext, Depends(get_auth_context)]) -> UserResponse:
    return UserResponse.from_user(context.user)


@router.patch("/me", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    context: Annotated[AuthContext, Depends(get_auth_context)],
    database: Annotated[Session, Depends(get_session)],
) -> UserResponse:
    user = context.user
    for field_name in ("full_name", "email", "company", "role", "experience_level"):
        value = getattr(payload, field_name)
        if value is not None:
            setattr(user, field_name, value.strip() if isinstance(value, str) else value)
    try:
        database.commit()
    except IntegrityError as exc:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc
    database.refresh(user)
    return UserResponse.from_user(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    context: Annotated[AuthContext, Depends(get_auth_context)],
    database: Annotated[Session, Depends(get_session)],
) -> Response:
    database.delete(context.auth_session)
    database.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
