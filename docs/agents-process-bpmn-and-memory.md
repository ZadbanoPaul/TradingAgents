# Proces agentów: BPMN (Mermaid), głębokość analizy, pamięć

Ten dokument opisuje **bieżący** przepływ LangGraph w TradingAgents oraz sposób budowania pamięci kontekstowej. Diagramy są w notacji zbliżonej do BPMN (Mermaid `flowchart` / `subgraph`).

## Gdzie jest kod

- Graf: `tradingagents/graph/setup.py`, logika pętli: `tradingagents/graph/conditional_logic.py`
- Domyślna kolejność analityków (instytucjonalna v2): `tradingagents/graph/trading_graph.py` (`_resolve_pipeline`)
- Stan: `tradingagents/agents/utils/agent_states.py`
- Pamięć BM25: `tradingagents/agents/utils/memory.py` (`FinancialSituationMemory`)

## Pipeline instytucjonalny v2 (domyślny)

Gdy `full_institutional_pipeline` w konfiguracji joba/grafu jest **true** (domyślnie w `default_config.py`), kolejność przed debatą to:

Orchestrator → Market → Social → News → Fundamentals → Accounting Quality → Valuation → Sector → Catalyst → *(opcjonalnie News Web, jeśli `enable_news_web_agent`)* → Data Quality → Scoring → Bull ↔ Bear → Research Manager → Trader → debata ryzyka → Portfolio Manager.

Ustawienie **false** przywraca tryb „tylko tablica `analysts` z joba” (np. cztery klasyczne analityki), bez wymuszania powyższej sekwencji.

## Pamięć (memory) — co trafia i na jak długo

- **W ramach jednego joba** agenci bull/bear/trader/research manager/portfolio manager używają instancji `FinancialSituationMemory`: dokumenty tekstowe + BM25 do wybierania `past_memory_str` w promptach.
- **Nie** jest to trwała baza „między jobami”: po zakończeniu procesu instancje są zwalniane wraz z grafem. Kolejny raport startuje **bez** automatycznego wczytania pamięci z poprzedniego zadania.
- **Trwały ślad** wyników: zapis joba w SQLite (`analysis_jobs.result_json`, `progress_json`) oraz artefakty transparentności (JSON przy wywołaniach LLM) — to osobna warstwa od BM25.

## Różnice głębokości (UI „Run in background”)

Parametry `max_debate_rounds` i `max_risk_discuss_rounds` sterują liczbą przejść w pętlach debaty inwestycyjnej (Bull ↔ Bear) oraz ryzyka (Aggressive ↔ Conservative ↔ Neutral). Im wyższa wartość, tym więcej wymian zanim węzeł przejdzie do Research Manager / Portfolio Manager.

W panelu **History** oba limity są ustawiane łącznie z polem `research_depth`:

- **shallow** → `max_debate_rounds = max_risk_discuss_rounds = 1`
- **medium** → oba `= 2`
- **deep** → oba `= 3`

Topologia **sekwencji analityków przed debatą** jest ustalana przez `_resolve_pipeline` (v2) lub listę `analysts` (tryb legacy). **Pętle** debaty inwestycyjnej i ryzyka nadal zależą wyłącznie od `ConditionalLogic` i limitów `max_*`.

---

## Diagram: shallow / medium / deep (ta sama ścieżka v2)

Różnica między shallow, medium i deep dotyczy **wyłącznie** liczby przejść w pętlach (Bull↔Bear, Aggressive↔Conservative↔Neutral), nie kolejności węzłów na diagramie.

```mermaid
flowchart TB
  START([Start joba]) --> O[Orchestrator Analyst]
  O --> A1[Market Analyst + tools]
  A1 --> A2[Social Analyst + tools]
  A2 --> A3[News Analyst + tools]
  A3 --> A4[Fundamentals Analyst + tools]
  A4 --> AQ[Accounting Quality + tools]
  AQ --> V[Valuation + tools]
  V --> SE[Sector Analyst + tools]
  SE --> CA[Catalyst Analyst + tools]
  CA --> DQ[Data Quality Analyst]
  DQ --> SC[Scoring Analyst]
  SC --> B[Bull Researcher]
  B --> C[Bear Researcher]
  C --> B
  C --> RM[Research Manager]
  RM --> T[Trader]
  T --> R1[Aggressive Risk]
  R1 --> R2[Conservative Risk]
  R2 --> R3[Neutral Risk]
  R3 --> R1
  R3 --> PM[Portfolio Manager]
  PM --> END([Koniec / sygnał])
```

## Opcjonalny agent `news_web`

Jeśli w konfiguracji joba `enable_news_web_agent: true`, węzeł **News Web Agent** (RSS) jest wstawiany **między Catalyst a Data Quality** w sekwencji `_resolve_pipeline` (domyślny pipeline v2).

## Kontrakt wyjść / placeholdery

- Lista placeholderów w promptach: endpoint `GET /api/prompts/placeholders` (źródło: `tradingagents/prompts/placeholders_registry.py`).
- Mapa slotów wyjściowych (tekst w `AgentState`, przyszły JSON wielopolowy): `GET /api/prompts/output-contract` (`tradingagents/prompts/agent_output_graph.py`).
