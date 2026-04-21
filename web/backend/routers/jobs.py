"""Kolejka raportów w tle — utworzenie i podgląd statusu."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from web.backend.config import get_settings
from web.backend.database import get_db
from web.backend.deps import get_current_user
from web.backend.models import AnalysisJob, StoredApiKey, User
from web.backend.schemas import JobCreate, JobDetail, JobOut

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _require_openai(db: Session, user: User) -> None:
    ok = (
        db.query(StoredApiKey)
        .filter(StoredApiKey.user_id == user.id, StoredApiKey.provider == "openai")
        .first()
    )
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Skonfiguruj klucz OpenAI w Ustawieniach (BYOK).",
        )


@router.post("", response_model=JobOut)
def create_job(
    body: JobCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    _require_openai(db, user)
    _lang_map = {"en": "English", "pl": "Polish"}
    analysts = list(body.analysts or [])
    if body.enable_news_web_agent and "news_web" not in analysts:
        analysts.append("news_web")

    cfg: dict[str, Any] = {
        "analysts": analysts,
        "investment_horizon": body.investment_horizon,
        "indicators_select_all": bool(body.indicators_select_all),
        "selected_indicators": list(body.selected_indicators or []),
        "news_query_mode": body.news_query_mode,
        "news_article_limit": int(body.news_article_limit),
        "news_date_from": body.news_date_from,
        "news_date_to": body.news_date_to,
        "news_recent_hours": int(body.news_recent_hours),
        "enable_news_web_agent": bool(body.enable_news_web_agent),
        "research_depth": body.research_depth,
        "llm_provider": body.llm_provider,
        "quick_think_llm": body.quick_think_llm,
        "deep_think_llm": body.deep_think_llm,
        "max_debate_rounds": body.max_debate_rounds,
        "max_risk_discuss_rounds": body.max_risk_discuss_rounds,
        "output_language": _lang_map.get(body.report_language, "English"),
        "report_language": body.report_language,
    }
    if body.reasoning is not None and str(body.reasoning).strip() != "":
        cfg["openai_reasoning_effort"] = str(body.reasoning).strip()
    job = AnalysisJob(
        user_id=user.id,
        ticker=body.ticker.strip().upper(),
        trade_date=body.trade_date.strip(),
        status="pending",
        background=bool(body.background),
        config_json=json.dumps(cfg, ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}/artifacts/download", response_class=FileResponse)
def download_job_artifact(
    job_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    relpath: str = Query(
        ...,
        description="Ścieżka względem katalogu danych, np. jobs/1/artifacts/00001_llm_request.json",
    ),
):
    job = db.get(AnalysisJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania.")
    prefix = f"jobs/{job_id}/artifacts/"
    if not relpath.startswith(prefix) or ".." in relpath:
        raise HTTPException(status_code=400, detail="Niedozwolona ścieżka artefaktu.")
    root = Path(get_settings()["data_dir"]).resolve()
    target = (root / relpath).resolve()
    if not str(target).startswith(str(root)) or not target.is_file():
        raise HTTPException(status_code=404, detail="Plik nie istnieje.")
    return FileResponse(
        path=str(target),
        media_type="application/json",
        filename=target.name,
    )


@router.get("", response_model=list[JobOut])
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = 100,
):
    q = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.user_id == user.id)
        .order_by(AnalysisJob.id.desc())
        .limit(min(limit, 500))
    )
    return list(q.all())


@router.get("/{job_id}", response_model=JobDetail)
def get_job(
    job_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    job = db.get(AnalysisJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania.")
    result = json.loads(job.result_json) if job.result_json else None
    cfg = json.loads(job.config_json) if job.config_json else None
    progress = json.loads(job.progress_json) if getattr(job, "progress_json", None) else None
    return JobDetail(
        id=job.id,
        ticker=job.ticker,
        trade_date=job.trade_date,
        status=job.status,
        background=job.background,
        final_signal=job.final_signal,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        duration_ms=job.duration_ms,
        result=result,
        config=cfg,
        progress=progress,
    )
