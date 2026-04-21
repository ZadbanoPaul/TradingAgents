"""Szybki skan „kandydatów” (OHLC / sygnał) — bez pełnego pipeline agentów."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from web.backend.deps import get_current_user
from web.backend.models import User
from web.backend.services.candidate_screen import (
    ScreenParams,
    default_universe_tickers,
    screen_candidates,
)

router = APIRouter(prefix="/api/screen", tags=["screening"])


class CandidatesBody(BaseModel):
    tickers: list[str] | None = Field(
        default=None,
        description="Opcjonalna lista tickerów; jeśli pusta — domyślny zestaw large-cap.",
    )
    lookback_days: int = Field(default=90, ge=5, le=365)
    max_tickers: int = Field(default=30, ge=1, le=80)


@router.post("/candidates")
def post_candidates_screen(
    body: CandidatesBody,
    user: Annotated[User, Depends(get_current_user)],
):
    _ = user
    tickers = body.tickers if body.tickers else default_universe_tickers(body.max_tickers)
    data = screen_candidates(
        ScreenParams(
            tickers=tickers,
            lookback_days=body.lookback_days,
            max_rows=body.max_tickers,
        )
    )
    return data
