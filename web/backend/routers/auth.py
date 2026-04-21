"""Rejestracja, logowanie, sesja cookie."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from web.backend.database import get_db
from web.backend.models import User
from web.backend.password_util import hash_password, verify_password
from web.backend.schemas import UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(
    request: Request,
    body: UserCreate,
    db: Annotated[Session, Depends(get_db)],
):
    allow = os.environ.get("TRADINGAGENTS_WEB_ALLOW_REGISTER", "0") == "1"
    n_users = db.scalar(select(func.count()).select_from(User))
    if n_users and n_users > 0 and not allow:
        raise HTTPException(
            status_code=403,
            detail="Rejestracja wyłączona. Użyj konta bootstrap lub ustaw TRADINGAGENTS_WEB_ALLOW_REGISTER=1.",
        )
    if db.scalar(select(User).where(User.username == body.username)):
        raise HTTPException(status_code=400, detail="Nazwa użytkownika zajęta.")
    u = User(
        username=body.username.strip(),
        password_hash=hash_password(body.password),
        display_name=body.display_name.strip() or body.username,
    )
    db.add(u)
    db.flush()
    request.session["user_id"] = u.id
    return u


@router.post("/login", response_model=UserOut)
def login(
    request: Request,
    body: UserLogin,
    db: Annotated[Session, Depends(get_db)],
):
    u = db.scalar(select(User).where(User.username == body.username))
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Błędny login lub hasło.")
    request.session["user_id"] = u.id
    return u


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=UserOut | None)
def me(request: Request, db: Annotated[Session, Depends(get_db)]):
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.get(User, int(uid))
