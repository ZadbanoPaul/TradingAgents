"""
Kontrakt wyjść agentów: domyślnie pojedyncza wiadomość (tekst LLM),
opcjonalnie struktura JSON z wieloma polami — każde pole może być
wstawione jako placeholder w kolejnym agencie (po rozszerzeniu silnika).

Obecny silnik LangGraph przekazuje stan przez pola ``AgentState`` (stringi),
a nie przez dynamiczne placeholdery z JSON — poniżej mapa logiczna
„kto produkuje → kto konsumuje”, zgodna z kodem w ``graph/setup.py``.
"""

from __future__ import annotations

# slot_id: opis, producent (węzeł), konsumenci (kolejne prompty / stan)
OUTPUT_SLOTS: list[dict[str, str | list[str]]] = [
    {
        "slot_id": "market_report",
        "description": "Raport techniczny (narzędzia OHLCV + wskaźniki).",
        "producer": "Market Analyst",
        "consumers": ["Bull Researcher", "Bear Researcher", "Trader", "Risk team", "Portfolio Manager (pośrednio)"],
        "state_key": "market_report",
    },
    {
        "slot_id": "sentiment_report",
        "producer": "Social Media Analyst",
        "consumers": ["Bull", "Bear", "Trader", "Risk"],
        "state_key": "sentiment_report",
    },
    {
        "slot_id": "news_report",
        "producer": "News Analyst",
        "consumers": ["Bull", "Bear", "Trader", "Risk"],
        "state_key": "news_report",
    },
    {
        "slot_id": "news_web_report",
        "producer": "News Web Agent",
        "consumers": ["Bull", "Bear", "Trader", "Risk (doklejane do bloku news)"],
        "state_key": "news_web_report",
    },
    {
        "slot_id": "fundamentals_report",
        "producer": "Fundamentals Analyst",
        "consumers": ["Bull", "Bear", "Trader", "Risk"],
        "state_key": "fundamentals_report",
    },
    {
        "slot_id": "orchestrator_report",
        "description": "Status procesu, konflikty, braki dowodów (Orchestrator).",
        "producer": "Orchestrator Analyst",
        "consumers": ["Research Manager", "Data Quality (kontekst)", "Scoring (kontekst)"],
        "state_key": "orchestrator_report",
    },
    {
        "slot_id": "accounting_quality_report",
        "description": "Jakość zysków i rachunkowości.",
        "producer": "Accounting Quality Analyst",
        "consumers": ["Bull", "Bear", "Research Manager", "Trader (annex)", "Risk (annex)", "Portfolio Manager", "Scoring"],
        "state_key": "accounting_quality_report",
    },
    {
        "slot_id": "valuation_report",
        "description": "Wycena względem fundamentów i scenariuszy.",
        "producer": "Valuation Analyst",
        "consumers": ["Bull", "Bear", "Research Manager", "Trader (annex)", "Risk (annex)", "Portfolio Manager", "Scoring"],
        "state_key": "valuation_report",
    },
    {
        "slot_id": "sector_report",
        "description": "Sektor i pozycja konkurencyjna.",
        "producer": "Sector Analyst",
        "consumers": ["Bull", "Bear", "Research Manager", "Trader (annex)", "Risk (annex)", "Portfolio Manager", "Scoring"],
        "state_key": "sector_report",
    },
    {
        "slot_id": "catalyst_report",
        "description": "Katalizatory i timing zdarzeń.",
        "producer": "Catalyst Analyst",
        "consumers": ["Bull", "Bear", "Research Manager", "Trader (annex)", "Risk (annex)", "Portfolio Manager", "Scoring"],
        "state_key": "catalyst_report",
    },
    {
        "slot_id": "data_quality_report",
        "description": "Ocena jakości danych i gotowości decyzji.",
        "producer": "Data Quality Analyst",
        "consumers": ["Research Manager", "Portfolio Manager", "Scoring"],
        "state_key": "data_quality_report",
    },
    {
        "slot_id": "scoring_report",
        "description": "Agregowana punktacja ważona.",
        "producer": "Scoring Analyst",
        "consumers": ["Research Manager", "Portfolio Manager"],
        "state_key": "scoring_report",
    },
    {
        "slot_id": "investment_plan",
        "producer": "Research Manager",
        "consumers": ["Trader", "Portfolio Manager"],
        "state_key": "investment_plan",
    },
    {
        "slot_id": "trader_investment_plan",
        "producer": "Trader",
        "consumers": ["Risk debators", "Portfolio Manager"],
        "state_key": "trader_investment_plan",
    },
    {
        "slot_id": "final_trade_decision",
        "producer": "Portfolio Manager",
        "consumers": ["Wynik joba / sygnał"],
        "state_key": "final_trade_decision",
    },
]

MULTI_OUTPUT_JSON_SCHEMA = {
    "title": "AgentStructuredOutput",
    "type": "object",
    "description": (
        "Opcjonalny format na przyszłość: jeden JSON z wieloma polami zamiast jednego bloku markdown. "
        "Klucze = slot_id z OUTPUT_SLOTS; wartości = string (fragment raportu)."
    ),
    "additionalProperties": {"type": "string"},
    "examples": [
        {
            "market_report": "## Trend…",
            "key_metrics_table": "| KPI | v |\n|---|---|",
        }
    ],
}


def describe_output_contract() -> dict:
    return {
        "default": "single_assistant_message",
        "optional_multi_field_json": MULTI_OUTPUT_JSON_SCHEMA,
        "slots": OUTPUT_SLOTS,
    }
