"""Katalog wskaźników technicznych (mapowanie na narzędzie get_indicators) + rekomendacje wg głębokości analizy."""

from __future__ import annotations

from typing import Literal

ResearchDepth = Literal["shallow", "medium", "deep"]
InvestmentHorizon = Literal["intraday", "swing_short", "swing_medium", "position", "long_term"]

INDICATOR_ENTRIES: list[dict[str, str]] = [
    {
        "id": "close_10_ema",
        "label": "EMA(10)",
        "category": "trend",
        "prompt_hint": (
            "Krótkoterminowa średnia krocząca wykładnicza (10 okresów). "
            "Wrażliwa na ostatnią cenę — do wejść/wyjść na małych interwałach; w trendzie silnym cena często „jedzie” po EMA."
        ),
    },
    {
        "id": "rsi",
        "label": "RSI",
        "category": "momentum",
        "prompt_hint": (
            "Wskaźnik siły względnej (momentum). Klasyczne progi 30/70; w silnym trendzie RSI może długo być w skrajnych strefach — "
            "interpretuj z kontekstem trendu i interwału."
        ),
    },
    {
        "id": "macd",
        "label": "MACD",
        "category": "momentum",
        "prompt_hint": (
            "Momentum z różnicy EMA; przecięcia linii MACD z sygnałem oraz histogram pokazują przyspieszenie/zwalnianie trendu."
        ),
    },
    {
        "id": "macds",
        "label": "MACD Signal",
        "category": "momentum",
        "prompt_hint": "Wygładzona linia sygnału MACD — używana razem z linią MACD do sygnałów przecięć.",
    },
    {
        "id": "macdh",
        "label": "MACD Histogram",
        "category": "momentum",
        "prompt_hint": "Różnica MACD–signal; do wczesnego wychwytywania słabnięcia trendu i dywergencji.",
    },
    {
        "id": "boll",
        "label": "Bollinger Middle (SMA20)",
        "category": "volatility",
        "prompt_hint": "Środek pasma Bollingera — benchmark zmienności wokół ceny.",
    },
    {
        "id": "boll_ub",
        "label": "Bollinger Upper",
        "category": "volatility",
        "prompt_hint": "Górna granica pasma — potencjalna strefa wykupienia lub wybicia w górę.",
    },
    {
        "id": "boll_lb",
        "label": "Bollinger Lower",
        "category": "volatility",
        "prompt_hint": "Dolna granica pasma — strefa wyprzedania lub kontynuacji spadku.",
    },
    {
        "id": "atr",
        "label": "ATR",
        "category": "volatility",
        "prompt_hint": (
            "Średni zasięg true range — miara zmienności do rozmiaru pozycji i stopów (nie kierunek trendu)."
        ),
    },
    {
        "id": "close_50_sma",
        "label": "SMA(50)",
        "category": "trend",
        "prompt_hint": "Średnioterminowy trend i dynamiczny poziom wsparcia/oporu.",
    },
    {
        "id": "close_200_sma",
        "label": "SMA(200)",
        "category": "trend",
        "prompt_hint": "Długoterminowy benchmark trendu (np. złote/przecinające się średnie).",
    },
    {
        "id": "vwma",
        "label": "VWMA",
        "category": "volume",
        "prompt_hint": "Średnia ważoną wolumenem — potwierdzanie trendu z udziałem płynności (yfinance/stockstats; Alpha Vantage może zwrócić komunikat ograniczenia).",
    },
    {
        "id": "mfi",
        "label": "MFI",
        "category": "volume",
        "prompt_hint": (
            "Money Flow Index — momentum z ceną i wolumenem; podobnie do RSI ale z wagą obrotu (dostępne w yfinance/stockstats)."
        ),
    },
]


def recommended_indicator_ids(depth: str, horizon: str) -> list[str]:
    """Rekomendowane zestawy: krótszy horyzont → szybsze wskaźniki; głębsza analiza → więcej warstw."""
    d = (depth or "medium").lower()
    h = (horizon or "swing_medium").lower()

    fast_pack = ["close_10_ema", "rsi", "macd", "macdh", "boll", "boll_ub", "boll_lb", "atr"]
    swing_pack = ["close_10_ema", "rsi", "macd", "macds", "macdh", "close_50_sma", "boll_ub", "boll_lb", "atr"]
    long_pack = ["close_50_sma", "close_200_sma", "rsi", "macd", "macdh", "boll", "atr", "mfi"]

    if h == "intraday":
        base = fast_pack
    elif h in ("swing_short",):
        base = fast_pack + ["close_50_sma"]
    elif h in ("swing_medium",):
        base = swing_pack
    else:
        base = long_pack

    if d == "shallow":
        return base[:5]
    if d == "medium":
        return base[:8]
    return base


def all_indicator_ids() -> list[str]:
    return [e["id"] for e in INDICATOR_ENTRIES]


def format_indicator_policy_for_market_prompt(cfg: dict) -> str:
    """Blok tekstu do system promptu analityka rynku (lista dozwolonych wskaźników)."""
    ids = resolve_user_indicator_selection(
        select_all=bool(cfg.get("indicators_select_all")),
        selected=list(cfg.get("selected_indicators") or []),
        depth=str(cfg.get("research_depth", "medium")),
        horizon=str(cfg.get("investment_horizon", "swing_medium")),
    )
    lines = [
        "**Konfiguracja zadania — wskaźniki techniczne (używaj dokładnie tych identyfikatorów w get_indicators):**",
        "",
    ]
    by_id = {e["id"]: e for e in INDICATOR_ENTRIES}
    for i in ids:
        meta = by_id.get(i)
        hint = (meta or {}).get("prompt_hint", "")
        lines.append(f"- `{i}` ({(meta or {}).get('label', i)}): {hint}")
    lines.extend(
        [
            "",
            "Wywołuj `get_indicators` osobno dla każdego identyfikatora (możesz podać kilka nazw oddzielonych przecinkiem w jednym wywołaniu).",
            "Nie wymyślaj identyfikatorów spoza listy — backend odfiltruje nieobsługiwane nazwy.",
        ]
    )
    return "\n".join(lines)


def resolve_user_indicator_selection(
    *,
    select_all: bool,
    selected: list[str] | None,
    depth: str,
    horizon: str,
) -> list[str]:
    if select_all:
        return all_indicator_ids()
    chosen = [x.strip().lower() for x in (selected or []) if x and str(x).strip()]
    if not chosen:
        return recommended_indicator_ids(depth, horizon)
    valid = set(all_indicator_ids())
    return [i for i in chosen if i in valid] or recommended_indicator_ids(depth, horizon)
