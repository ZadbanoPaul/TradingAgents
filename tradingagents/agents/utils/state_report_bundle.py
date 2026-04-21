"""Skrócone paczki raportów ze stanu dla promptów debaty / RM / PM."""


def news_with_web(state: dict) -> str:
    n = state.get("news_report") or ""
    nw = (state.get("news_web_report") or "").strip()
    if nw:
        return f"{n}\n\n--- News Web (RSS) ---\n{nw}"
    return n


def extended_reports_block(state: dict) -> str:
    """Dodatkowe raporty v2 dla promptów tekstowych (nie wszystkie muszą być wypełnione)."""
    parts = []
    mapping = [
        ("Orchestrator", "orchestrator_report"),
        ("Accounting quality", "accounting_quality_report"),
        ("Valuation", "valuation_report"),
        ("Sector / competition", "sector_report"),
        ("Catalysts", "catalyst_report"),
        ("Data quality", "data_quality_report"),
        ("Scoring", "scoring_report"),
    ]
    for title, key in mapping:
        v = (state.get(key) or "").strip()
        if v:
            parts.append(f"### {title}\n{v[:8000]}")
    return "\n\n".join(parts) if parts else ""
