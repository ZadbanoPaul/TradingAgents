"""Połączenie z bazą SQLite i sesją SQLAlchemy."""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from web.backend.config import get_settings

Base = declarative_base()
_engine = None
_SessionLocal = None


def _bootstrap_admin() -> None:
    import os as _os

    from web.backend.models import User
    from web.backend.password_util import hash_password

    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        n = db.scalar(select(func.count()).select_from(User))
        if n and n > 0:
            return
        bu = _os.environ.get("TRADINGAGENTS_WEB_BOOTSTRAP_USER", "").strip()
        bp = _os.environ.get("TRADINGAGENTS_WEB_BOOTSTRAP_PASSWORD", "")
        if not bu or not bp:
            return
        db.add(
            User(
                username=bu,
                password_hash=hash_password(bp),
                display_name=bu,
            )
        )
        db.commit()
    finally:
        db.close()


def init_db() -> None:
    global _engine, _SessionLocal
    path = get_settings()["db_path"]
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    _engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    from web.backend import models  # noqa: F401

    Base.metadata.create_all(bind=_engine)
    _ensure_analysis_jobs_schema()
    _SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=_engine, class_=Session, future=True
    )
    _bootstrap_admin()


def _ensure_analysis_jobs_schema() -> None:
    """Migracje lightweight (SQLite) — kolumny dodawane po pierwszym deployu."""
    from sqlalchemy import inspect, text

    assert _engine is not None
    insp = inspect(_engine)
    if not insp.has_table("analysis_jobs"):
        return
    cols = {c["name"] for c in insp.get_columns("analysis_jobs")}
    with _engine.begin() as conn:
        if "progress_json" not in cols:
            conn.execute(
                text("ALTER TABLE analysis_jobs ADD COLUMN progress_json TEXT")
            )


def get_db() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        init_db()
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def raw_session() -> Session:
    """Sesja bez auto-commit (dla workera)."""
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()
