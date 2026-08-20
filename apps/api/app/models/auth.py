from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import CreatedAtMixin, UuidPrimaryKeyMixin, utc_now


class User(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "experience_level IN ('guided', 'advanced')",
            name="ck_users_experience_level",
        ),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    company: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    experience_level: Mapped[str] = mapped_column(String(16), nullable=False, default="guided")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSession(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "user_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    user: Mapped[User] = relationship(back_populates="sessions")
