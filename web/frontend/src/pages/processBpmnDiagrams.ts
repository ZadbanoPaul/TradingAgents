/** Źródła Mermaid (flowchart) — shallow / medium / deep. */

export const PROCESS_INTRO = `
flowchart TB
  classDef note fill:#1c1917,stroke:#52525b,color:#e4e4e7;
  N1:::note["Uwaga: topologia grafu jest stała; zmienia się wyłącznie liczba przejść w pętlach debaty (Bull↔Bear) i ryzyka (A↔C↔N) — patrz job: max_debate_rounds / max_risk_discuss_rounds."]
`;

export const SHALLOW_CORE = `
flowchart TB
  START([Start joba]) --> M[Market + tools]
  M --> S[Social + tools]
  S --> N[News + tools]
  N --> F[Fundamentals + tools]
  F --> B[Bull Researcher]
  B --> C[Bear Researcher]
  C --> B
  C --> RM[Research Manager]
  RM --> T[Trader]
  T --> A[Aggressive]
  A --> C2[Conservative]
  C2 --> N2[Neutral]
  N2 --> A
  N2 --> PM[Portfolio Manager]
  PM --> END([Wynik joba])
`;

export const MEDIUM_CORE = `
flowchart TB
  START([Start joba]) --> M[Market + tools]
  M --> S[Social + tools]
  S --> N[News + tools]
  N --> F[Fundamentals + tools]
  F --> B[Bull Researcher]
  B --> C[Bear Researcher]
  C --> B
  C --> RM[Research Manager]
  RM --> T[Trader]
  T --> A[Aggressive]
  A --> C2[Conservative]
  C2 --> N2[Neutral]
  N2 --> A
  N2 --> PM[Portfolio Manager]
  PM --> END([Wynik joba])
  classDef hl fill:#14532d,stroke:#4ade80,color:#ecfccb;
  B:::hl
  C:::hl
  A:::hl
  C2:::hl
  N2:::hl
`;

export const DEEP_CORE = `
flowchart TB
  START([Start joba]) --> M[Market + tools]
  M --> S[Social + tools]
  S --> N[News + tools]
  N --> F[Fundamentals + tools]
  F --> B[Bull Researcher]
  B --> C[Bear Researcher]
  C --> B
  C --> RM[Research Manager]
  RM --> T[Trader]
  T --> A[Aggressive]
  A --> C2[Conservative]
  C2 --> N2[Neutral]
  N2 --> A
  N2 --> PM[Portfolio Manager]
  PM --> END([Wynik joba])
  classDef hl fill:#422006,stroke:#fb923c,color:#ffedd5;
  B:::hl
  C:::hl
  A:::hl
  C2:::hl
  N2:::hl
`;
