"""Zależności FastAPI (sesja DB, użytkownik z cookie sesji)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from web.backend.database import get_db
from web.backend.models import User


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Brak sesji — zaloguj się.")
    user = db.get(User, int(uid))
    if not user:
        raise HTTPException(status_code=401, detail="Nieprawidłowa sesja.")
    return user


OptionalUser = User | None


def get_optional_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> OptionalUser:
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.get(User, int(uid))
