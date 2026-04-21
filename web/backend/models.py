"""Modele ORM dla panelu web i kolejki raportów."""

from __future__ import annotations

import datetime as dt
from datetime import timezone

from sqlalchemy import (
    BigInteger,
    BLOB,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from web.backend.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    display_name: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(timezone.utc)
    )

    jobs: Mapped[list["AnalysisJob"]] = relationship(back_populates="user")
    api_keys: Mapped[list["StoredApiKey"]] = relationship(back_populates="user")
    prompts: Mapped[list["PromptOverride"]] = relationship(back_populates="user")
    prompt_version_rows: Mapped[list["PromptVersion"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class StoredApiKey(Base):
    __tablename__ = "stored_api_keys"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(64))
    ciphertext: Mapped[bytes] = mapped_column(BLOB)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="api_keys")


class PromptOverride(Base):
    __tablename__ = "prompt_overrides"
    __table_args__ = (UniqueConstraint("user_id", "prompt_key", name="uq_user_prompt"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    prompt_key: Mapped[str] = mapped_column(String(128), index=True)
    body: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="prompts")


class PromptVersion(Base):
    """Historia wersji promptu — jedna aktywna na (użytkownik, klucz)."""

    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("user_id", "prompt_key", "version", name="uq_user_prompt_version_no"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    prompt_key: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(timezone.utc)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user: Mapped["User"] = relationship(back_populates="prompt_version_rows")


class AnalysisJob(Base):
    """Raport w tle — niezależny od sesji przeglądarki."""

    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    trade_date: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True
    )  # pending | running | completed | failed
    background: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[str] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_signal: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON: lista kroków {ts, title, lines[]}
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(timezone.utc)
    )
    started_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    user: Mapped["User"] = relationship(back_populates="jobs")
