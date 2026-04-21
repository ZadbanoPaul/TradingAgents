import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { TickerAutocomplete } from "../components/TickerAutocomplete";
import { INDICATOR_OPTIONS, INVESTMENT_HORIZONS } from "../analysisOptions";
import { Jobs, Llm, type JobOut } from "../api";

/** Zgodnie z API OpenAI: ``reasoning.effort`` tylko dla modeli rozumujących (o-*, gpt-5*). */
function supportsOpenAiReasoningEffort(modelId: string): boolean {
  const m = modelId.trim().toLowerCase();
  if (!m) return false;
  if (m.startsWith("o1") || m.startsWith("o2") || m.startsWith("o3") || m.startsWith("o4")) return true;
  if (m.startsWith("gpt-5")) return true;
  return false;
}

const FALLBACK_OPENAI_MODELS: { id: string; label: string }[] = [
  { id: "gpt-4o-mini", label: "gpt-4o-mini" },
  { id: "gpt-4o", label: "gpt-4o" },
  { id: "gpt-4.1", label: "gpt-4.1" },
  { id: "gpt-4.1-mini", label: "gpt-4.1-mini" },
  { id: "o4-mini", label: "o4-mini (reasoning)" },
  { id: "o3", label: "o3 (reasoning)" },
  { id: "o3-mini", label: "o3-mini (reasoning)" },
];

function ModelSelect({
  label,
  value,
  onPick,
  modelChoices,
}: {
  label: string;
  value: string;
  onPick: (id: string) => void;
  modelChoices: { id: string; label: string }[];
}) {
  const withCurrent =
    value && !modelChoices.some((m) => m.id === value)
      ? [{ id: value, label: `${value} (niestandardowy)` }, ...modelChoices]
      : modelChoices;
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-zinc-500 font-mono">{label}</span>
      <select
        className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm text-zinc-200 cursor-pointer"
        value={value}
        onChange={(e) => onPick(e.target.value)}
      >
        {withCurrent.map((m) => (
          <option key={m.id} value={m.id}>
            {m.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function decisionColor(sig: string | null) {
  if (!sig) return "text-zinc-500";
  if (/sell|underweight/i.test(sig)) return "text-red-400";
  if (/buy|overweight/i.test(sig)) return "text-mint";
  return "text-zinc-300";
}

export default function History() {
  const [rows, setRows] = useState<JobOut[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    ticker: "MSFT",
    trade_date: new Date().toISOString().slice(0, 10),
    research_depth: "deep",
    investment_horizon: "swing_medium",
    indicators_select_all: false,
    selected_indicators: [] as string[],
    news_query_mode: "daterange" as "daterange" | "count",
    news_article_limit: 25,
    news_date_from: "",
    news_date_to: "",
    news_recent_hours: 48,
    enable_news_web_agent: false,
    llm_provider: "openai",
    quick_think_llm: "gpt-4o-mini",
    deep_think_llm: "gpt-4o",
    reasoning: "" as "" | "low" | "medium" | "high",
    report_language: "en" as "en" | "pl",
  });
  const [openaiModels, setOpenaiModels] = useState<{ id: string; label: string }[]>([]);

  async function refresh() {
    setBusy(true);
    setErr(null);
    try {
      setRows(await Jobs.list());
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Błąd");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { models } = await Llm.openaiModels();
        if (!cancelled) {
          setOpenaiModels(
            models
              .filter((m) => m.id)
              .map((m) => ({ id: m.id, label: m.label || m.id }))
              .slice(0, 30)
          );
        }
      } catch {
        if (!cancelled) setOpenaiModels([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const modelChoices = useMemo(
    () => (openaiModels.length > 0 ? openaiModels : FALLBACK_OPENAI_MODELS),
    [openaiModels]
  );

  const reasoningApplicable = useMemo(
    () =>
      supportsOpenAiReasoningEffort(form.quick_think_llm) ||
      supportsOpenAiReasoningEffort(form.deep_think_llm),
    [form.quick_think_llm, form.deep_think_llm]
  );

  useEffect(() => {
    if (!reasoningApplicable && form.reasoning) {
      setForm((f) => ({ ...f, reasoning: "" }));
    }
  }, [reasoningApplicable, form.reasoning]);

  async function runAnalysis() {
    setErr(null);
    const depth = form.research_depth;
    const maxDeb = depth === "deep" ? 3 : depth === "medium" ? 2 : 1;
    try {
      await Jobs.create({
        ticker: form.ticker,
        trade_date: form.trade_date,
        background: true,
        analysts: ["market", "social", "news", "fundamentals"],
        investment_horizon: form.investment_horizon,
        indicators_select_all: form.indicators_select_all,
        selected_indicators: form.indicators_select_all ? [] : form.selected_indicators,
        news_query_mode: form.news_query_mode,
        news_article_limit: form.news_article_limit,
        news_date_from: form.news_date_from || null,
        news_date_to: form.news_date_to || null,
        news_recent_hours: form.news_recent_hours,
        enable_news_web_agent: form.enable_news_web_agent,
        research_depth: depth,
        llm_provider: form.llm_provider,
        quick_think_llm: form.quick_think_llm,
        deep_think_llm: form.deep_think_llm,
        max_debate_rounds: maxDeb,
        max_risk_discuss_rounds: maxDeb,
        report_language: form.report_language,
        ...(form.reasoning && reasoningApplicable ? { reasoning: form.reasoning } : {}),
      });
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Błąd");
    }
  }

  return (
    <div className="max-w-6xl space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-mono text-mint">Report History</h1>
        <button
          type="button"
          onClick={() => refresh()}
          disabled={busy}
          className="rounded-md border border-mint/40 px-4 py-2 text-sm font-mono text-mint hover:bg-mint/10 disabled:opacity-50"
        >
          Check for new reports
        </button>
      </div>

      <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-950/50 space-y-4">
        <h2 className="text-mint font-mono">Run in background</h2>
        <p className="text-xs text-zinc-500 font-mono">
          Raporty są zapisywane w bazie i realizowane przez workera — możesz zamknąć
          przeglądarkę.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 items-end">
          <TickerAutocomplete
            value={form.ticker}
            onChange={(ticker) => setForm({ ...form, ticker })}
            placeholder="Ticker (np. MSFT)"
          />
          <input
            type="date"
            className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm"
            value={form.trade_date}
            onChange={(e) => setForm({ ...form, trade_date: e.target.value })}
          />
          <select
            className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm cursor-pointer"
            value={form.research_depth}
            onChange={(e) => setForm({ ...form, research_depth: e.target.value })}
          >
            <option value="shallow">Shallow</option>
            <option value="medium">Medium</option>
            <option value="deep">Deep</option>
          </select>
          <label className="flex flex-col gap-1 sm:col-span-2 xl:col-span-2">
            <span className="text-xs text-zinc-500 font-mono">Horyzont inwestycyjny (okna danych + news)</span>
            <select
              className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm cursor-pointer"
              value={form.investment_horizon}
              onChange={(e) => setForm({ ...form, investment_horizon: e.target.value })}
            >
              {INVESTMENT_HORIZONS.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.label}
                </option>
              ))}
            </select>
          </label>
          <div className="sm:col-span-2 xl:col-span-4 border border-zinc-800 rounded-md p-3 space-y-2 bg-black/20">
            <p className="text-xs text-mint font-mono">Wskaźniki techniczne (get_indicators)</p>
            <p className="text-[11px] text-zinc-500 font-mono">
              Backend dobiera rekomendowany zestaw wg głębokości i horyzontu. Możesz wymusić własny wybór lub „wszystkie”.
            </p>
            <label className="flex items-center gap-2 text-xs font-mono text-zinc-300 cursor-pointer">
              <input
                type="checkbox"
                checked={form.indicators_select_all}
                onChange={(e) =>
                  setForm({ ...form, indicators_select_all: e.target.checked, selected_indicators: [] })
                }
              />
              Wszystkie dostępne wskaźniki
            </label>
            {!form.indicators_select_all && (
              <div className="max-h-36 overflow-y-auto grid grid-cols-2 sm:grid-cols-3 gap-1 text-[11px]">
                {INDICATOR_OPTIONS.map((o) => (
                  <label key={o.id} className="flex items-center gap-1 text-zinc-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.selected_indicators.includes(o.id)}
                      onChange={(e) => {
                        const on = e.target.checked;
                        setForm({
                          ...form,
                          selected_indicators: on
                            ? [...form.selected_indicators, o.id]
                            : form.selected_indicators.filter((x) => x !== o.id),
                        });
                      }}
                    />
                    {o.label}
                  </label>
                ))}
              </div>
            )}
          </div>
          <div className="sm:col-span-2 xl:col-span-4 border border-zinc-800 rounded-md p-3 space-y-2 bg-black/20">
            <p className="text-xs text-mint font-mono">Źródło newsów (API / yfinance wg konfiguracji dostawcy)</p>
            <div className="flex flex-wrap gap-3 text-xs font-mono text-zinc-300">
              <label className="flex items-center gap-1 cursor-pointer">
                <input
                  type="radio"
                  name="nqm"
                  checked={form.news_query_mode === "daterange"}
                  onChange={() => setForm({ ...form, news_query_mode: "daterange" })}
                />
                Zakres dat
              </label>
              <label className="flex items-center gap-1 cursor-pointer">
                <input
                  type="radio"
                  name="nqm"
                  checked={form.news_query_mode === "count"}
                  onChange={() => setForm({ ...form, news_query_mode: "count" })}
                />
                Limit artykułów (steruje też AV limit)
              </label>
            </div>
            <label className="flex flex-col gap-1 max-w-xs">
              <span className="text-[11px] text-zinc-500">Limit / liczba artykułów</span>
              <input
                type="number"
                min={1}
                max={200}
                className="rounded-md border border-zinc-700 bg-black/40 px-2 py-1 font-mono text-sm"
                value={form.news_article_limit}
                onChange={(e) => setForm({ ...form, news_article_limit: Number(e.target.value) || 1 })}
              />
            </label>
            {form.news_query_mode === "daterange" && (
              <div className="flex flex-wrap gap-2">
                <input
                  type="date"
                  className="rounded-md border border-zinc-700 bg-black/40 px-2 py-1 font-mono text-xs"
                  value={form.news_date_from}
                  onChange={(e) => setForm({ ...form, news_date_from: e.target.value })}
                />
                <span className="text-zinc-600 self-center">—</span>
                <input
                  type="date"
                  className="rounded-md border border-zinc-700 bg-black/40 px-2 py-1 font-mono text-xs"
                  value={form.news_date_to}
                  onChange={(e) => setForm({ ...form, news_date_to: e.target.value })}
                />
              </div>
            )}
            <label className="flex flex-col gap-1 max-w-xs">
              <span className="text-[11px] text-zinc-500">
                Okno news (godziny wstecz) — intraday / swing krótki
              </span>
              <input
                type="number"
                min={6}
                max={240}
                className="rounded-md border border-zinc-700 bg-black/40 px-2 py-1 font-mono text-sm"
                value={form.news_recent_hours}
                onChange={(e) => setForm({ ...form, news_recent_hours: Number(e.target.value) || 48 })}
              />
            </label>
          </div>
          <label className="flex items-center gap-2 sm:col-span-2 text-xs font-mono text-zinc-300 cursor-pointer">
            <input
              type="checkbox"
              checked={form.enable_news_web_agent}
              onChange={(e) => setForm({ ...form, enable_news_web_agent: e.target.checked })}
            />
            Agent News Web (RSS Google News — bez dodatkowego klucza API)
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-zinc-500 font-mono">Język raportu</span>
            <select
              className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm cursor-pointer"
              value={form.report_language}
              onChange={(e) =>
                setForm({
                  ...form,
                  report_language: e.target.value as "en" | "pl",
                })
              }
            >
              <option value="en">English (EN)</option>
              <option value="pl">Polski (PL)</option>
            </select>
          </label>
          <ModelSelect
            label="Model szybki (quick)"
            value={form.quick_think_llm}
            modelChoices={modelChoices}
            onPick={(id) => setForm({ ...form, quick_think_llm: id })}
          />
          <ModelSelect
            label="Model głęboki (deep)"
            value={form.deep_think_llm}
            modelChoices={modelChoices}
            onPick={(id) => setForm({ ...form, deep_think_llm: id })}
          />
          <label className="flex flex-col gap-1">
            <span className="text-xs text-zinc-500 font-mono">
              Reasoning effort{" "}
              {!reasoningApplicable && (
                <span className="text-zinc-600">(niedostępne dla wybranych modeli)</span>
              )}
            </span>
            <select
              className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              disabled={!reasoningApplicable}
              title="OpenAI: reasoning.effort = low | medium | high — tylko dla modeli o-*/gpt-5* (Responses API)."
              value={form.reasoning}
              onChange={(e) =>
                setForm({
                  ...form,
                  reasoning: e.target.value as typeof form.reasoning,
                })
              }
            >
              <option value="">Domyślny (API / model)</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
          </label>
          <button
            type="button"
            onClick={runAnalysis}
            className="rounded-md bg-mint py-2 text-sm font-semibold text-black sm:col-span-2 lg:col-span-1"
          >
            Queue analysis
          </button>
        </div>
        <p className="text-xs text-zinc-600 font-mono">
          Modele: API <code className="text-zinc-500">/api/llm/openai/models</code> lub lista zapasowa.
          Parametr <code className="text-zinc-500">reasoning_effort</code> jest wysyłany wyłącznie do wywołań
          modeli <strong>o1–o4</strong> oraz <strong>gpt-5*</strong>; dla GPT-4.x / 4o nie jest ustawiany (unik 400).
        </p>
        {err && <p className="text-sm text-red-400 font-mono">{err}</p>}
      </div>

      <div className="border border-zinc-800 rounded-lg p-4 text-xs text-zinc-500 font-mono">
        Akcje: podgląd szczegółów w kolumnie linku · status ukończenia w kolorze mint
      </div>

      <div className="overflow-x-auto border border-zinc-800 rounded-lg">
        <table className="w-full text-left text-sm font-mono">
          <thead className="bg-zinc-900 text-zinc-400">
            <tr>
              <th className="p-3">ID</th>
              <th className="p-3">Ticker</th>
              <th className="p-3">Cutoff</th>
              <th className="p-3">Decision</th>
              <th className="p-3">Status</th>
              <th className="p-3">Created</th>
              <th className="p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-zinc-800 hover:bg-zinc-900/40">
                <td className="p-3 text-zinc-500">{r.id}</td>
                <td className="p-3">{r.ticker}</td>
                <td className="p-3 text-zinc-400">{r.trade_date}</td>
                <td className={`p-3 ${decisionColor(r.final_signal)}`}>
                  {r.final_signal || "—"}
                </td>
                <td className="p-3 text-zinc-400">{r.status}</td>
                <td className="p-3 text-zinc-500 whitespace-nowrap">
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td className="p-3">
                  <Link
                    to={`/live/${r.id}`}
                    className="text-mint hover:underline text-xs"
                  >
                    View details
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <p className="p-8 text-center text-zinc-500 font-mono text-sm">
            Brak wpisów.
          </p>
        )}
      </div>
    </div>
  );
}
