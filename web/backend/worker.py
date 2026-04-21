"""Proces workera: przetwarza kolejkę ``pending`` w SQLite (niezależnie od sesji WWW)."""

from __future__ import annotations

import logging
import time

from sqlalchemy import select

from web.backend.database import init_db, raw_session
from web.backend.job_runner import run_job
from web.backend.models import AnalysisJob

logging.basicConfig(level=logging.INFO)
logging.getLogger("web.backend.job_runner").setLevel(logging.INFO)
log = logging.getLogger("tradingagents.worker")


def claim_next_job_id() -> int | None:
    db = raw_session()
    try:
        row = db.execute(
            select(AnalysisJob.id)
            .where(AnalysisJob.status == "pending")
            .order_by(AnalysisJob.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        return int(row) if row is not None else None
    finally:
        db.close()


def main() -> None:
    init_db()
    log.info("Worker Zadbano investing masters — start pętli kolejki.")
    while True:
        jid = claim_next_job_id()
        if jid is None:
            time.sleep(2.0)
            continue
        db = raw_session()
        try:
            run_job(db, jid)
            db.commit()
        except Exception:
            db.rollback()
            log.exception("Błąd przy job_id=%s", jid)
        finally:
            db.close()


if __name__ == "__main__":
    main()
