"""Lista i zapis promptów (per użytkownik) + wersjonowanie, placeholdery, kontrakt wyjść."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts.agent_output_graph import describe_output_contract
from tradingagents.prompts.placeholders_registry import list_placeholders
from web.backend.database import get_db
from web.backend.deps import get_current_user
from web.backend.models import PromptVersion, User
from web.backend.prompt_catalog import list_prompt_items
from web.backend.prompt_versions_service import (
    activate_version,
    active_bodies_map,
    clear_all_versions_and_override,
    delete_version,
    list_versions,
    save_new_version,
    version_to_api,
)
from web.backend.schemas import (
    PromptItem,
    PromptSave,
    PromptVersionDetail,
    PromptVersionSummary,
)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

_VALID = set(prompt_keys.ALL_PROMPT_KEYS)


@router.get("/placeholders")
def get_placeholders(_user: User = Depends(get_current_user)):
    del _user
    return {"placeholders": list_placeholders()}


@router.get("/output-contract")
def get_output_contract(_user: User = Depends(get_current_user)):
    del _user
    return describe_output_contract()


@router.get("/prompt-versions/{row_id}", response_model=PromptVersionDetail)
def get_prompt_version_row(
    row_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    row = (
        db.query(PromptVersion)
        .filter(PromptVersion.id == row_id, PromptVersion.user_id == user.id)
        .one_or_none()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Wersja nie istnieje.")
    return PromptVersionDetail(
        id=row.id,
        prompt_key=row.prompt_key,
        version=row.version,
        created_at=row.created_at.isoformat() if row.created_at else "",
        is_active=bool(row.is_active),
        body=row.body or "",
    )


@router.post("/prompt-versions/{row_id}/activate", response_model=PromptVersionSummary)
def post_activate_prompt_version(
    row_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    row = activate_version(db, user.id, row_id)
    if not row:
        raise HTTPException(status_code=404, detail="Wersja nie istnieje.")
    return PromptVersionSummary(**version_to_api(row))


@router.delete("/prompt-versions/{row_id}")
def delete_prompt_version_row(
    row_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    ok, reason = delete_version(db, user.id, row_id)
    if not ok and reason == "not_found":
        raise HTTPException(status_code=404, detail="Wersja nie istnieje.")
    if not ok and reason == "active":
        raise HTTPException(
            status_code=400,
            detail="Nie można usunąć aktywnej wersji — najpierw ustaw inną jako aktywną.",
        )
    return {"ok": True}


@router.get("/{prompt_key}/versions", response_model=list[PromptVersionSummary])
def list_prompt_versions(
    prompt_key: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if prompt_key not in _VALID:
        raise HTTPException(status_code=400, detail="Nieznany klucz promptu.")
    rows = list_versions(db, user.id, prompt_key)
    return [PromptVersionSummary(**version_to_api(v)) for v in rows]


@router.get("", response_model=list[PromptItem])
def list_prompts(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    # Aktywne wersje + legacy (bez wersji) — spójnie z workerem
    overrides = active_bodies_map(db, user.id)
    return list_prompt_items(overrides)


@router.put("", response_model=PromptItem)
def save_prompt(
    body: PromptSave,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if body.key not in _VALID:
        raise HTTPException(status_code=400, detail="Nieznany identyfikator promptu.")
    save_new_version(db, user.id, body.key, body.body)
    items = list_prompt_items(active_bodies_map(db, user.id))
    for it in items:
        if it["key"] == body.key:
            return PromptItem(**it)
    raise HTTPException(status_code=500, detail="Błąd zapisu.")


@router.delete("/{prompt_key}")
def reset_prompt(
    prompt_key: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if prompt_key not in _VALID:
        raise HTTPException(status_code=400, detail="Nieznany klucz.")
    clear_all_versions_and_override(db, user.id, prompt_key)
    return {"ok": True}
