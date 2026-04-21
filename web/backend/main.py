"""Punkt wejścia API + serwowanie SPA."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from web.backend.config import get_settings
from web.backend.database import init_db
from web.backend.instrument_registry import ensure_instrument_rows
from web.backend.routers import (
    auth,
    data_catalog,
    instruments,
    jobs,
    market_preview,
    openai_meta,
    prompts,
    settings_keys,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    async def _warm_instruments() -> None:
        try:
            await asyncio.to_thread(ensure_instrument_rows)
        except Exception:
            pass

    asyncio.create_task(_warm_instruments())
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Zadbano investing masters", lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings["session_secret"],
        max_age=14 * 24 * 3600,
        same_site="lax",
        https_only=False,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings["cors_origins"] if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(settings_keys.router)
    app.include_router(prompts.router)
    app.include_router(openai_meta.router)
    app.include_router(instruments.router)
    app.include_router(jobs.router)
    app.include_router(market_preview.router)
    app.include_router(data_catalog.router)

    static_dir = Path(__file__).resolve().parent / "static" / "dist"
    assets = static_dir / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        if full_path.startswith("api"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404)
        index = static_dir / "index.html"
        if index.is_file():
            return FileResponse(index)
        return FileResponse(
            Path(__file__).resolve().parent / "static" / "placeholder.html"
        )

    return app


app = create_app()
