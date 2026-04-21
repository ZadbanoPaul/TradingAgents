export type ProgressRow = Record<string, unknown> & {
  ts?: string;
  type?: string;
  title?: string;
  lines?: string[];
  /** Krok sekwencji grafu (job_runner) */
  step_no?: number;
  /** Heurystyczna etykieta agenta / węzła */
  agent_label?: string;
};
