"""Szyfrowanie wartości wrażliwych (Fernet, klucz z sekretu aplikacji)."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from web.backend.config import get_settings


def _fernet() -> Fernet:
    raw = get_settings()["encryption_secret"].encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
    return Fernet(key)


def encrypt_text(plain: str) -> bytes:
    return _fernet().encrypt(plain.encode("utf-8"))


def decrypt_text(blob: bytes) -> str:
    return _fernet().decrypt(blob).decode("utf-8")
