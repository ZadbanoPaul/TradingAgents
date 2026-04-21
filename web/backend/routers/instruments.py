"""Instrumenty / autouzupełnianie walorów."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from web.backend.deps import get_current_user
from web.backend.instrument_registry import ensure_instrument_rows, search_instruments
from web.backend.models import User

router = APIRouter(prefix="/api/instruments", tags=["instruments"])


@router.get("/count")
def instruments_count(
    user: Annotated[User, Depends(get_current_user)],
):
    """Liczba załadowanych instrumentów (po pierwszym odświeżeniu cache)."""
    rows = ensure_instrument_rows()
    return {"count": len(rows)}


@router.get("/autocomplete")
def instruments_autocomplete(
    user: Annotated[User, Depends(get_current_user)],
    q: str = Query(..., min_length=1, max_length=64, description="Fragment symbolu lub nazwy"),
    limit: int = Query(25, ge=1, le=100),
):
    """Propozycje symboli: dopasowanie po skrócie (prefiks / zawiera) oraz po nazwie papieru."""
    suggestions = search_instruments(q, limit=limit)
    return {"suggestions": suggestions}
