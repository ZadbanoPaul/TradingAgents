"""Opisy kroków grafu LangGraph dla użytkownika (log postępu) + etykieta agenta / węzła."""

from __future__ import annotations

from typing import Any


def _msg_preview(m: Any, limit: int = 320) -> str:
    c = getattr(m, "content", None)
    if c is None:
        s = str(m)
    elif isinstance(c, str):
        s = c
    elif isinstance(c, list):
        parts = []
        for block in c:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        s = "\n".join(parts)
    else:
        s = str(c)
    s = s.replace("\r\n", "\n").strip()
    if len(s) > limit:
        return s[: limit - 1] + "…"
    return s


def _msg_label(m: Any) -> str:
    t = getattr(m, "type", None) or getattr(m, "role", None) or "message"
    name = getattr(m, "name", None)
    if name:
        return f"{t}/{name}"
    return str(t)


def _str_len(x: Any) -> int:
    if isinstance(x, str):
        return len(x)
    return 0


# Kolejność ma znaczenie przy remisie — pierwszy największy przyrost wygrywa.
_REPORT_AGENTS: list[tuple[str, str]] = [
    ("orchestrator_report", "Orchestrator Analyst"),
    ("market_report", "Market Analyst (techniczny)"),
    ("sentiment_report", "Social / Sentiment Analyst"),
    ("news_report", "News / Macro Analyst"),
    ("news_web_report", "News Web (RSS)"),
    ("fundamentals_report", "Fundamentals Analyst"),
    ("accounting_quality_report", "Accounting Quality Analyst"),
    ("valuation_report", "Valuation Analyst"),
    ("sector_report", "Sector / Competition Analyst"),
    ("catalyst_report", "Catalyst Analyst"),
    ("data_quality_report", "Data Quality Analyst"),
    ("scoring_report", "Scoring Analyst"),
]


def infer_graph_actor(prev: dict[str, Any] | None, cur: dict[str, Any]) -> str:
    """Heurystyka: który agent „dominował” w kroku, na podstawie przyrostu pól stanu."""
    if prev is None:
        return "Bootstrap grafu"
    best_label = "LangGraph (węzeł pomocniczy / narzędzia)"
    best_delta = -1
    for key, label in _REPORT_AGENTS:
        a, b = _str_len(prev.get(key)), _str_len(cur.get(key))
        d = b - a
        if d > best_delta:
            best_delta = d
            best_label = label
    if best_delta > 0:
        return best_label

    for key, label in [
        ("investment_plan", "Research Manager"),
        ("trader_investment_plan", "Trader"),
        ("final_trade_decision", "Portfolio Manager"),
    ]:
        a, b = _str_len(prev.get(key)), _str_len(cur.get(key))
        if b > a:
            return label

    pmsgs = prev.get("messages") or []
    cmsgs = cur.get("messages") or []
    if isinstance(cmsgs, list) and len(cmsgs) > (len(pmsgs) if isinstance(pmsgs, list) else 0):
        last = cmsgs[-1]
        nm = getattr(last, "name", None)
        if nm:
            return f"LLM ({nm})"
        return f"LLM ({_msg_label(last)})"

    ids = cur.get("investment_debate_state")
    pids = prev.get("investment_debate_state")
    if isinstance(ids, dict):
        h = str(ids.get("history", "") or "")
        ph = str((pids or {}).get("history", "") or "") if isinstance(pids, dict) else ""
        if len(h) > len(ph):
            return "Debaty: Bull / Bear"

    rds = cur.get("risk_debate_state")
    prds = prev.get("risk_debate_state")
    if isinstance(rds, dict):
        h = str(rds.get("history", "") or "")
        ph = str((prds or {}).get("history", "") or "") if isinstance(prds, dict) else ""
        if len(h) > len(ph):
            return "Debaty ryzyka (A / N / C)"

    return best_label


def describe_state_transition(
    prev: dict[str, Any] | None, cur: dict[str, Any]
) -> list[str]:
    """Zwraca linie opisu „co się zmieniło” między dwoma pełnymi stanami (stream_mode=values)."""
    lines: list[str] = []
    actor = infer_graph_actor(prev, cur)
    lines.append(f"Agent / węzeł (heurystyka): {actor}")

    if prev is None:
        lines.append(
            f"Uruchomiono pipeline dla {cur.get('company_of_interest', '?')} "
            f"(data: {cur.get('trade_date', '?')})."
        )
        lines.append(
            "Uwaga: wiele kolejnych kroków z komunikatem „bez zmian raportów” to zwykle "
            "wywołania narzędzi (ToolNode) lub czyszczenie wiadomości — celowe przy pełnym pipeline."
        )
        return lines

    for key, label in _REPORT_AGENTS:
        a, b = _str_len(prev.get(key)), _str_len(cur.get(key))
        if b > a:
            lines.append(f"{label}: zapisano raport ({b} znaków, +{b - a}).")

    text_keys = [
        ("investment_plan", "Research Manager — plan / werdykt debaty"),
        ("trader_investment_plan", "Trader — propozycja transakcji"),
        ("final_trade_decision", "Portfolio Manager — decyzja końcowa"),
    ]
    for key, label in text_keys:
        a, b = _str_len(prev.get(key)), _str_len(cur.get(key))
        if b > a:
            lines.append(f"{label}: zaktualizowano ({b} znaków).")

    pmsgs = prev.get("messages") or []
    cmsgs = cur.get("messages") or []
    if isinstance(cmsgs, list) and len(cmsgs) > (
        len(pmsgs) if isinstance(pmsgs, list) else 0
    ):
        last = cmsgs[-1]
        lines.append(
            f"LLM / agent: {_msg_label(last)} — {_msg_preview(last, 400)}"
        )

    ids = cur.get("investment_debate_state")
    pids = prev.get("investment_debate_state")
    if isinstance(ids, dict):
        h = str(ids.get("history", "") or "")
        ph = str((pids or {}).get("history", "") or "") if isinstance(pids, dict) else ""
        if len(h) > len(ph):
            lines.append(
                f"Debaty inwestycyjne: nowy wpis (+{len(h) - len(ph)} znaków historii)."
            )

    rds = cur.get("risk_debate_state")
    prds = prev.get("risk_debate_state")
    if isinstance(rds, dict):
        h = str(rds.get("history", "") or "")
        ph = str((prds or {}).get("history", "") or "") if isinstance(prds, dict) else ""
        if len(h) > len(ph):
            lines.append(
                f"Debaty ryzyka: nowy wpis (+{len(h) - len(ph)} znaków historii)."
            )

    if len(lines) <= 1:
        lines.append(
            "Krok grafu: brak przyrostu raportów tekstowych — typowo wywołanie narzędzia, "
            "wewnętrzny krok LangGraph lub przygotowanie kontekstu LLM."
        )

    return lines


def normalize_stream_chunk(raw: Any) -> dict[str, Any] | None:
    """LangGraph może zwracać dict lub krotkę (tryb, stan)."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, tuple) and len(raw) >= 2 and isinstance(raw[1], dict):
        return raw[1]
    return None
