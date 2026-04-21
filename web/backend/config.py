"""Konfiguracja aplikacji webowej (zmienne środowiskowe)."""

from __future__ import annotations

import os
from functools import lru_cache


def _data_dir() -> str:
    return os.environ.get(
        "TRADINGAGENTS_WEB_DATA_DIR",
        os.path.join(os.path.expanduser("~"), ".tradingagents", "web"),
    )


@lru_cache
def get_settings() -> dict:
    """Ustawienia tylko do odczytu (cache procesu)."""
    return {
        "data_dir": _data_dir(),
        "db_path": os.environ.get(
            "TRADINGAGENTS_WEB_DB",
            os.path.join(_data_dir(), "app.db"),
        ),
        "session_secret": os.environ.get(
            "TRADINGAGENTS_WEB_SESSION_SECRET", "change-me-in-production"
        ),
        "encryption_secret": os.environ.get(
            "TRADINGAGENTS_WEB_ENCRYPTION_SECRET", "change-me-32bytes-minimum!!"
        ),
        "cors_origins": os.environ.get(
            "TRADINGAGENTS_WEB_CORS", "http://127.0.0.1:5173,http://localhost:5173"
        ).split(","),
    }
