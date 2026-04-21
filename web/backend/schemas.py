"""Schematy Pydantic dla API REST."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=128)
    password: str = Field(min_length=6, max_length=256)
    display_name: str = Field(default="", max_length=256)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str

    class Config:
        from_attributes = True


class ApiKeyUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None


class ApiKeyStatus(BaseModel):
    openai_configured: bool
    alpha_vantage_configured: bool


class PromptItem(BaseModel):
    key: str
    title: str
    description: str
    default_body: str
    current_body: str


class PromptSave(BaseModel):
    key: str
    body: str


class PromptVersionSummary(BaseModel):
    id: int
    prompt_key: str
    version: int
    created_at: str
    is_active: bool
    preview: str


class PromptVersionDetail(BaseModel):
    id: int
    prompt_key: str
    version: int
    created_at: str
    is_active: bool
    body: str


class JobCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    trade_date: str = Field(description="YYYY-MM-DD")
    background: bool = True
    analysts: list[str] = Field(
        default_factory=lambda: ["market", "social", "news", "fundamentals"]
    )
    investment_horizon: str = Field(
        default="swing_medium",
        description="intraday | swing_short | swing_medium | position | long_term",
    )
    indicators_select_all: bool = Field(default=False)
    selected_indicators: list[str] = Field(default_factory=list)
    news_query_mode: str = Field(default="daterange", description="daterange | count")
    news_article_limit: int = Field(default=25, ge=1, le=200)
    news_date_from: Optional[str] = Field(default=None, description="YYYY-MM-DD gdy news_query_mode=daterange")
    news_date_to: Optional[str] = Field(default=None, description="YYYY-MM-DD gdy news_query_mode=daterange")
    news_recent_hours: int = Field(
        default=48,
        ge=6,
        le=240,
        description="Dla intraday/swing_short: okno news w godzinach (gdy brak jawnych dat).",
    )
    enable_news_web_agent: bool = Field(
        default=False,
        description="Dodaje agenta news_web z narzędziem RSS Google News.",
    )
    research_depth: str = Field(default="medium")  # shallow | medium | deep
    llm_provider: str = Field(default="openai")
    quick_think_llm: str = Field(default="gpt-4o-mini")
    deep_think_llm: str = Field(default="gpt-4o")
    max_debate_rounds: int = Field(default=1, ge=0, le=5)
    max_risk_discuss_rounds: int = Field(default=1, ge=0, le=5)
    reasoning: Optional[str] = Field(
        default=None,
        description=(
            "OpenAI Responses API: reasoning.effort = low | medium | high. "
            "Stosowane wyłącznie dla modeli wspierających ten parametr (np. o-*, gpt-5*); "
            "dla GPT-4.x / 4o backend pomija ustawienie."
        ),
    )
    report_language: Literal["en", "pl"] = Field(
        default="en",
        description="Wersja językowa raportu: en → English, pl → Polish (output_language w workerze).",
    )
    instrument_meta: Optional[dict[str, Any]] = Field(
        default=None,
        description="Opcjonalne pola kontekstu instrumentu (v2): company_name, exchange, sector, benchmark, limity ryzyka itd.",
    )
    full_institutional_pipeline: Optional[bool] = Field(
        default=None,
        description="Jeśli podane, nadpisuje domyślną pełną ścieżkę instytucjonalną (false = tylko analysts z joba).",
    )


class PortfolioSynthesisJobCreate(BaseModel):
    """Kolejka joba typu „synteza portfela LLM” (agregacja zakończonych analiz jednego tickera)."""

    source_job_ids: list[int] = Field(min_length=1, description="ID zakończonych jobów (completed)")
    notional_usd: float = Field(gt=0, description="Nominał portfela w USD")
    num_positions: int = Field(default=8, ge=1, le=64)
    include_minute_last_day: bool = Field(
        default=False,
        description="Opcjonalne próbki świec 1m (ostatni dzień) — jak w portfolio-draft.",
    )
    trade_date: Optional[str] = Field(
        default=None,
        description="YYYY-MM-DD zapisywany w wierszu joba; domyślnie dzisiaj (UTC).",
    )
    max_context_chars: int = Field(default=90_000, ge=5000, le=200_000)
    report_language: Literal["en", "pl"] = Field(
        default="en",
        description="Język syntezy LLM.",
    )
    llm_provider: str = Field(default="openai")
    quick_think_llm: str = Field(default="gpt-4o-mini")
    deep_think_llm: str = Field(default="gpt-4o")
    reasoning: Optional[str] = Field(
        default=None,
        description="OpenAI: reasoning.effort dla modeli wspierających parametr.",
    )
    background: bool = Field(default=True, description="Zachowane dla spójności API (job zawsze w tle).")


class JobOut(BaseModel):
    id: int
    ticker: str
    trade_date: str
    status: str
    background: bool
    final_signal: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


class JobDetail(JobOut):
    result: Optional[dict[str, Any]] = None
    config: Optional[dict[str, Any]] = None
    progress: Optional[list[dict[str, Any]]] = None
