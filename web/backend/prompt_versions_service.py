"""Logika wersji promptów: numer wersji, stempel czasu, aktywna wersja, synchronizacja z ``PromptOverride``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from web.backend.models import PromptOverride, PromptVersion


def backfill_version_from_override(db: Session, user_id: int, prompt_key: str) -> None:
    """Jeśli brak wersji, a istnieje legacy ``PromptOverride`` — utwórz wersję 1."""
    if (
        db.query(PromptVersion)
        .filter(PromptVersion.user_id == user_id, PromptVersion.prompt_key == prompt_key)
        .count()
        > 0
    ):
        return
    row = (
        db.query(PromptOverride)
        .filter(PromptOverride.user_id == user_id, PromptOverride.prompt_key == prompt_key)
        .one_or_none()
    )
    if not row:
        return
    db.add(
        PromptVersion(
            user_id=user_id,
            prompt_key=prompt_key,
            version=1,
            body=row.body,
            is_active=True,
        )
    )


def list_versions(db: Session, user_id: int, prompt_key: str) -> list[PromptVersion]:
    backfill_version_from_override(db, user_id, prompt_key)
    return (
        db.query(PromptVersion)
        .filter(PromptVersion.user_id == user_id, PromptVersion.prompt_key == prompt_key)
        .order_by(PromptVersion.version.desc())
        .all()
    )


def _sync_override(db: Session, user_id: int, prompt_key: str, body: str) -> None:
    row = (
        db.query(PromptOverride)
        .filter(PromptOverride.user_id == user_id, PromptOverride.prompt_key == prompt_key)
        .one_or_none()
    )
    if row:
        row.body = body
        row.updated_at = datetime.now(timezone.utc)
    else:
        db.add(PromptOverride(user_id=user_id, prompt_key=prompt_key, body=body))


def save_new_version(db: Session, user_id: int, prompt_key: str, body: str) -> PromptVersion:
    """Nowa wersja (max+1), aktywna; pozostałe dezaktywowane."""
    max_v = (
        db.query(func.max(PromptVersion.version))
        .filter(PromptVersion.user_id == user_id, PromptVersion.prompt_key == prompt_key)
        .scalar()
    )
    next_v = int(max_v or 0) + 1
    db.query(PromptVersion).filter(
        PromptVersion.user_id == user_id,
        PromptVersion.prompt_key == prompt_key,
    ).update({PromptVersion.is_active: False})
    ver = PromptVersion(
        user_id=user_id,
        prompt_key=prompt_key,
        version=next_v,
        body=body,
        is_active=True,
    )
    db.add(ver)
    _sync_override(db, user_id, prompt_key, body)
    return ver


def activate_version(db: Session, user_id: int, version_id: int) -> PromptVersion | None:
    row = (
        db.query(PromptVersion)
        .filter(PromptVersion.id == version_id, PromptVersion.user_id == user_id)
        .one_or_none()
    )
    if not row:
        return None
    db.query(PromptVersion).filter(
        PromptVersion.user_id == user_id,
        PromptVersion.prompt_key == row.prompt_key,
    ).update({PromptVersion.is_active: False})
    row.is_active = True
    _sync_override(db, user_id, row.prompt_key, row.body)
    return row


def delete_version(db: Session, user_id: int, version_id: int) -> tuple[bool, str]:
    row = (
        db.query(PromptVersion)
        .filter(PromptVersion.id == version_id, PromptVersion.user_id == user_id)
        .one_or_none()
    )
    if not row:
        return False, "not_found"
    if row.is_active:
        return False, "active"
    db.delete(row)
    return True, "ok"


def clear_all_versions_and_override(db: Session, user_id: int, prompt_key: str) -> None:
    db.query(PromptVersion).filter(
        PromptVersion.user_id == user_id,
        PromptVersion.prompt_key == prompt_key,
    ).delete()
    row = (
        db.query(PromptOverride)
        .filter(PromptOverride.user_id == user_id, PromptOverride.prompt_key == prompt_key)
        .one_or_none()
    )
    if row:
        db.delete(row)


def active_bodies_map(db: Session, user_id: int) -> dict[str, str]:
    """Mapa prompt_key → treść aktywnej wersji (lub legacy override)."""
    out: dict[str, str] = {}
    rows = (
        db.query(PromptVersion)
        .filter(PromptVersion.user_id == user_id, PromptVersion.is_active.is_(True))
        .all()
    )
    for r in rows:
        out[r.prompt_key] = r.body
    legacy = db.query(PromptOverride).filter(PromptOverride.user_id == user_id).all()
    for r in legacy:
        if r.prompt_key not in out:
            out[r.prompt_key] = r.body
    return out


def version_to_api(v: PromptVersion) -> dict[str, Any]:
    return {
        "id": v.id,
        "prompt_key": v.prompt_key,
        "version": v.version,
        "created_at": v.created_at.isoformat() if v.created_at else "",
        "is_active": bool(v.is_active),
        "preview": (v.body or "")[:160].replace("\n", " "),
    }
