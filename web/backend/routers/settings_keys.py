"""Przechowywanie kluczy API (zaszyfrowane)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from web.backend.crypto_store import encrypt_text
from web.backend.database import get_db
from web.backend.deps import get_current_user
from web.backend.models import StoredApiKey, User
from web.backend.schemas import ApiKeyStatus, ApiKeyUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _upsert_key(db: Session, user: User, provider: str, value: str | None) -> None:
    row = (
        db.query(StoredApiKey)
        .filter(StoredApiKey.user_id == user.id, StoredApiKey.provider == provider)
        .one_or_none()
    )
    if value is None or value.strip() == "":
        if row:
            db.delete(row)
        return
    blob = encrypt_text(value.strip())
    if row:
        row.ciphertext = blob
        row.verified = True
    else:
        db.add(
            StoredApiKey(
                user_id=user.id,
                provider=provider,
                ciphertext=blob,
                verified=True,
            )
        )


def _has_key(db: Session, user: User, provider: str) -> bool:
    return (
        db.query(StoredApiKey)
        .filter(StoredApiKey.user_id == user.id, StoredApiKey.provider == provider)
        .first()
        is not None
    )


@router.get("/api-keys", response_model=ApiKeyStatus)
def api_key_status(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return ApiKeyStatus(
        openai_configured=_has_key(db, user, "openai"),
        alpha_vantage_configured=_has_key(db, user, "alpha_vantage"),
    )


@router.put("/api-keys", response_model=ApiKeyStatus)
def save_api_keys(
    body: ApiKeyUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if body.openai_api_key is not None:
        _upsert_key(db, user, "openai", body.openai_api_key or None)
    if body.alpha_vantage_api_key is not None:
        _upsert_key(db, user, "alpha_vantage", body.alpha_vantage_api_key or None)
    db.commit()
    return ApiKeyStatus(
        openai_configured=_has_key(db, user, "openai"),
        alpha_vantage_configured=_has_key(db, user, "alpha_vantage"),
    )
