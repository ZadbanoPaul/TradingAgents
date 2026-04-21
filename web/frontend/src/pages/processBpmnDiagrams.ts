/** Źródła Mermaid (flowchart) — shallow / medium / deep (ta sama topologia v2; różne podświetlenia). */

export const PROCESS_INTRO = `
flowchart TB
  classDef note fill:#1c1917,stroke:#52525b,color:#e4e4e7;
  N1:::note["Uwaga: domyślnie pełna ścieżka instytucjonalna v2 (trading_graph._resolve_pipeline). Wyłączenie: full_institutional_pipeline=false w config joba — wtedy używana jest lista analysts z joba. Pętle debaty (Bull↔Bear) i ryzyka (A↔C↔N) zależą od max_debate_rounds / max_risk_discuss_rounds. News Web RSS jest wstawiany między Catalyst a Data Quality tylko gdy enable_news_web_agent."]
`;

/** Węzły (wspólne dla shallow/medium/deep) — jeden blok ``flowchart TB`` na diagram. */
const INSTITUTIONAL_BODY = `
  START([Start joba]) --> O[Orchestrator Analyst]
  O --> M[Market Analyst + tools]
  M --> S[Social Analyst + tools]
  S --> N[News Analyst + tools]
  N --> F[Fundamentals Analyst + tools]
  F --> AQ[Accounting Quality + tools]
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
  T --> A[Aggressive Risk]
  A --> C2[Conservative Risk]
  C2 --> N2[Neutral Risk]
  N2 --> A
  N2 --> PM[Portfolio Manager]
  PM --> END([Wynik joba])
`;

export const SHALLOW_CORE = `
flowchart TB
${INSTITUTIONAL_BODY}
`;

export const MEDIUM_CORE = `
flowchart TB
${INSTITUTIONAL_BODY}
  classDef hl fill:#14532d,stroke:#4ade80,color:#ecfccb;
  B:::hl
  C:::hl
  A:::hl
  C2:::hl
  N2:::hl
`;

export const DEEP_CORE = `
flowchart TB
${INSTITUTIONAL_BODY}
  classDef hl fill:#422006,stroke:#fb923c,color:#ffedd5;
  B:::hl
  C:::hl
  A:::hl
  C2:::hl
  N2:::hl
`;
