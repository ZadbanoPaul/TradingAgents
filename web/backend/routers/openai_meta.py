"""Lista modeli OpenAI — tylko modele sensowne do analizy tekstu (chat / reasoning)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tradingagents.llm_clients.model_catalog import MODEL_OPTIONS

from web.backend.crypto_store import decrypt_text
from web.backend.database import get_db
from web.backend.deps import get_current_user
from web.backend.models import StoredApiKey, User

router = APIRouter(prefix="/api/llm", tags=["llm"])

_MAX_MODELS = 10

_EXCLUDE = (
    "whisper",
    "tts",
    "dall-e",
    "dall",
    "embedding",
    "moderation",
    "davinci",
    "babbage",
    "ada",
    "curie",
    "cushman",
    "audio",
    "realtime",
    "transcribe",
    "speech",
    "image",
    "search",
    "instruct",
    "similarity",
    "edit",
    "code-search",
    "if-",
    "ft:",
    "fine-tuning",
    "computer-use",
    "o1-pro",  # drogie preview — pomijamy w krótkiej liście
)


def _is_text_chat_model(model_id: str) -> bool:
    m = model_id.lower().strip()
    if not m or m.startswith("ft:"):
        return False
    if any(x in m for x in _EXCLUDE):
        return False
    # Rodziny używane do chat / completion z tekstem
    prefixes = (
        "gpt-5",
        "gpt-4.1",
        "gpt-4o",
        "gpt-4-",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1",
        "o2",
        "o3",
        "o4",
        "chatgpt-4o",
    )
    return m.startswith(prefixes)


def _catalog_openai_ids() -> list[str]:
    """Katalog projektu (m.in. GPT-5.4) — zawsze proponowane, nawet gdy /v1/models jeszcze ich nie zwraca."""
    seen: list[str] = []
    for mode in ("quick", "deep"):
        for _label, mid in MODEL_OPTIONS.get("openai", {}).get(mode, []):
            if not mid or mid == "custom":
                continue
            if mid not in seen:
                seen.append(mid)
    return [m for m in seen if _is_text_chat_model(m)]


def _label_for(id_: str) -> str:
    for mode in ("quick", "deep"):
        for label, mid in MODEL_OPTIONS.get("openai", {}).get(mode, []):
            if mid == id_:
                return label
    return id_


@router.get("/openai/models")
def list_openai_models(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    row = (
        db.query(StoredApiKey)
        .filter(StoredApiKey.user_id == user.id, StoredApiKey.provider == "openai")
        .first()
    )
    if not row or not row.ciphertext:
        raise HTTPException(
            status_code=400,
            detail="Brak klucza OpenAI — dodaj go w API Keys.",
        )
    try:
        api_key = decrypt_text(row.ciphertext)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Odszyfrowanie klucza: {e}") from e

    req = urllib.request.Request(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    api_ids: set[str] = set()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        data = body.get("data") or []
        for m in data:
            mid = str(m.get("id", "") or "").strip()
            if mid and _is_text_chat_model(mid):
                api_ids.add(mid)
    except urllib.error.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI API: HTTP {e.code} — {e.read().decode('utf-8', errors='replace')[:500]}",
        ) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(e)) from e

    ordered: list[str] = []
    # 1) Katalog (np. gpt-5.4*) na początku
    for mid in _catalog_openai_ids():
        if mid not in ordered:
            ordered.append(mid)
    # 2) Dopisz z API, które przeszły filtr
    for mid in sorted(api_ids):
        if mid not in ordered:
            ordered.append(mid)

    # Krótka lista — tylko kilka rozsądnych do analizy tekstu
    final_ids = ordered[:_MAX_MODELS]

    return {
        "models": [{"id": mid, "label": _label_for(mid)} for mid in final_ids],
        "note": (
            "Lista skrócona do modeli chat/reasoning; wykluczono embeddingi, audio, obrazy itd. "
            "Identyfikatory z katalogu projektu (np. GPT-5.4) są dołączane nawet jeśli endpoint /v1/models "
            "nie zwraca jeszcze danej nazwy dla Twojego konta — przy błędzie 404 przy wywołaniu chat sprawdź dostępność w dokumentacji OpenAI."
        ),
    }
