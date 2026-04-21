const base = "";

async function api<T>(
  path: string,
  opts: RequestInit & { json?: unknown } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string>),
  };
  let body: BodyInit | undefined =
    opts.body === null || opts.body === undefined ? undefined : opts.body;
  if (opts.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.json);
  }
  const r = await fetch(`${base}${path}`, {
    ...opts,
    headers,
    body,
    credentials: "include",
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  if (r.status === 204) return undefined as T;
  return r.json() as Promise<T>;
}

export type User = { id: number; username: string; display_name: string };

export const Auth = {
  me: () => api<User | null>("/api/auth/me"),
  login: (username: string, password: string) =>
    api<User>("/api/auth/login", { method: "POST", json: { username, password } }),
  logout: () => api<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
  register: (username: string, password: string, display_name: string) =>
    api<User>("/api/auth/register", {
      method: "POST",
      json: { username, password, display_name },
    }),
};

export type ApiKeyStatus = {
  openai_configured: boolean;
  alpha_vantage_configured: boolean;
};

export const Settings = {
  keys: () => api<ApiKeyStatus>("/api/settings/api-keys"),
  saveKeys: (body: {
    openai_api_key?: string | null;
    alpha_vantage_api_key?: string | null;
  }) => api<ApiKeyStatus>("/api/settings/api-keys", { method: "PUT", json: body }),
};

export type PromptItem = {
  key: string;
  title: string;
  description: string;
  default_body: string;
  current_body: string;
};

export const Prompts = {
  list: () => api<PromptItem[]>("/api/prompts"),
  save: (key: string, body: string) =>
    api<PromptItem>("/api/prompts", { method: "PUT", json: { key, body } }),
  reset: (key: string) =>
    api<{ ok: boolean }>(`/api/prompts/${encodeURIComponent(key)}`, {
      method: "DELETE",
    }),
};

export type PromptVersionSummary = {
  id: number;
  prompt_key: string;
  version: number;
  created_at: string;
  is_active: boolean;
  preview: string;
};

export type PromptVersionDetail = PromptVersionSummary & { body: string };

export type PlaceholderRow = { id: string; description: string; context: string };

export const PromptVersions = {
  list: (promptKey: string) =>
    api<PromptVersionSummary[]>(
      `/api/prompts/${encodeURIComponent(promptKey)}/versions`
    ),
  getRow: (rowId: number) =>
    api<PromptVersionDetail>(`/api/prompts/prompt-versions/${rowId}`),
  activate: (rowId: number) =>
    api<PromptVersionSummary>(`/api/prompts/prompt-versions/${rowId}/activate`, {
      method: "POST",
    }),
  remove: (rowId: number) =>
    api<{ ok: boolean }>(`/api/prompts/prompt-versions/${rowId}`, { method: "DELETE" }),
};

export const PromptMeta = {
  placeholders: () => api<{ placeholders: PlaceholderRow[] }>("/api/prompts/placeholders"),
  outputContract: () => api<Record<string, unknown>>("/api/prompts/output-contract"),
};

export const DataCatalog = {
  avSeries: () =>
    api<{ series: Record<string, unknown>[]; source_doc: string }>("/api/data-catalog/av-series"),
  avCacheStats: () => api<Record<string, unknown>>("/api/data-catalog/av-cache-stats"),
};

export const MarketPreview = {
  ohlcv: (ticker: string, days = 180) =>
    api<{ ticker: string; rows: Record<string, unknown>[] }>(
      `/api/preview/ohlcv?ticker=${encodeURIComponent(ticker)}&days=${days}`
    ),
};

export type JobOut = {
  id: number;
  ticker: string;
  trade_date: string;
  status: string;
  background: boolean;
  final_signal: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
};

export type JobDetail = JobOut & {
  result: Record<string, unknown> | null;
  config: Record<string, unknown> | null;
  progress?: Record<string, unknown>[] | null;
};

export type OpenAiModelRow = { id: string; label?: string };

export const Llm = {
  openaiModels: () =>
    api<{ models: OpenAiModelRow[]; note?: string }>("/api/llm/openai/models"),
};

export type InstrumentSuggestion = { symbol: string; name: string };

export const Instruments = {
  autocomplete: (q: string, limit = 35) =>
    api<{ suggestions: InstrumentSuggestion[] }>(
      `/api/instruments/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`
    ),
};

export const Jobs = {
  list: () => api<JobOut[]>("/api/jobs"),
  create: (body: Record<string, unknown>) =>
    api<JobOut>("/api/jobs", { method: "POST", json: body }),
  createPortfolioSynthesis: (body: {
    source_job_ids: number[];
    notional_usd: number;
    num_positions?: number;
    include_minute_last_day?: boolean;
    trade_date?: string;
    max_context_chars?: number;
    report_language?: "en" | "pl";
    llm_provider?: string;
    quick_think_llm?: string;
    deep_think_llm?: string;
    reasoning?: string | null;
    background?: boolean;
  }) =>
    api<JobOut>("/api/jobs/portfolio-synthesis", { method: "POST", json: body }),
  get: (id: number) => api<JobDetail>(`/api/jobs/${id}`),
};

export type CandidateRow = Record<string, unknown>;

export const Screen = {
  candidates: (body: {
    tickers?: string[] | null;
    lookback_days?: number;
    max_tickers?: number;
  }) =>
    api<{
      as_of: string;
      lookback_days: number;
      universe_note: string;
      rows: CandidateRow[];
      errors: string[];
    }>("/api/screen/candidates", { method: "POST", json: body }),
};

export type CompletedJobRow = {
  id: number;
  ticker: string;
  trade_date: string;
  final_signal: string | null;
  created_at: string | null;
  duration_ms: number | null;
};

export const Insights = {
  completedJobs: (params: { date_from?: string; date_to?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params.date_from) q.set("date_from", params.date_from);
    if (params.date_to) q.set("date_to", params.date_to);
    if (params.limit != null) q.set("limit", String(params.limit));
    const qs = q.toString();
    return api<{ jobs: CompletedJobRow[] }>(
      `/api/insights/completed-jobs${qs ? `?${qs}` : ""}`
    );
  },
  portfolioDraft: (body: {
    job_ids: number[];
    notional_usd?: number;
    num_positions?: number;
    include_minute_last_day?: boolean;
  }) =>
    api<Record<string, unknown>>("/api/insights/portfolio-draft", {
      method: "POST",
      json: body,
    }),
};
