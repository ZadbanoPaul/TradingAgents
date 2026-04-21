"""Historia analiz (jobów) i szkic portfela z wybranych raportów."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from web.backend.database import get_db
from web.backend.deps import get_current_user
from web.backend.models import User
from web.backend.services.historical_insights import (
    build_portfolio_draft,
    list_completed_jobs,
)

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/completed-jobs")
def get_completed_jobs(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(200, ge=1, le=500),
):
    return {"jobs": list_completed_jobs(db, user.id, date_from, date_to, limit)}


class PortfolioDraftBody(BaseModel):
    job_ids: list[int] = Field(..., min_length=1, max_length=48)
    notional_usd: float = Field(default=100_000, gt=0)
    num_positions: int = Field(default=8, ge=1, le=32)
    include_minute_last_day: bool = Field(
        default=False,
        description="Dla kilku pierwszych walorów: próba pobrania świec 1m (yfinance; limity).",
    )


@router.post("/portfolio-draft")
def post_portfolio_draft(
    body: PortfolioDraftBody,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return build_portfolio_draft(
        db,
        user.id,
        body.job_ids,
        body.notional_usd,
        body.num_positions,
        body.include_minute_last_day,
    )
