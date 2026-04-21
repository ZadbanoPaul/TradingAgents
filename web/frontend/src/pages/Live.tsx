import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { Jobs, type JobDetail } from "../api";
import { TransparencyProgress } from "../components/TransparencyProgress";
import type { ProgressRow } from "../types/progress";

const REPORT_KEYS: { key: string; label: string }[] = [
  { key: "market_report", label: "Raport: rynek (techniczny)" },
  { key: "sentiment_report", label: "Raport: social / sentyment" },
  { key: "news_report", label: "Raport: newsy" },
  { key: "news_web_report", label: "Raport: News Web (RSS)" },
  { key: "fundamentals_report", label: "Raport: fundamenty" },
  { key: "investment_plan", label: "Research Manager" },
  { key: "trader_investment_plan", label: "Trader" },
  { key: "final_trade_decision", label: "Decyzja końcowa (Portfolio Manager)" },
];

export default function Live() {
  const { id } = useParams();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [openReport, setOpenReport] = useState<string | null>(null);

  const poll = useCallback(async () => {
    if (!id) return null;
    const j = await Jobs.get(Number(id));
    setJob(j);
    return j;
  }, [id]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    let t: ReturnType<typeof setTimeout>;

    async function loop() {
      if (cancelled) return;
      try {
        const j = await poll();
        if (cancelled || !j) return;
        const delay =
          j.status === "pending" || j.status === "running" ? 1500 : 12000;
        t = setTimeout(loop, delay);
      } catch (e) {
        if (!cancelled) {
          setErr(e instanceof Error ? e.message : "Błąd");
          t = setTimeout(loop, 5000);
        }
      }
    }
    loop();
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [id, poll]);

  const decision = job?.result?.final_trade_decision as string | undefined;
  const progress = (job?.progress ?? []) as ProgressRow[];

  return (
    <div className="max-w-5xl space-y-8 pb-16">
      <Link to="/history" className="text-sm font-mono text-mint hover:underline">
        ← Back to History
      </Link>
      <div>
        <h1 className="text-2xl font-mono text-mint">Report #{id}</h1>
        {job && (
          <p className="mt-1">
            <Link
              to={`/live/${job.id}/charts`}
              className="text-xs font-mono text-mint hover:underline"
            >
              Strona wykresów (załącznik analityczny) →
            </Link>
          </p>
        )}
        {job?.config && (
          <div className="mt-3 text-xs font-mono text-zinc-500 border border-zinc-800 rounded-md p-3 overflow-x-auto">
            <p className="text-mint mb-2">Konfiguracja zadania (kontrola)</p>
            <table className="w-full text-left border-collapse">
              <tbody>
                {(
                  [
                    ["report_language", job.config.report_language ?? "—"],
                    ["output_language", job.config.output_language ?? "—"],
                    ["investment_horizon", job.config.investment_horizon ?? "—"],
                    ["indicators_select_all", String(job.config.indicators_select_all ?? false)],
                    ["selected_indicators", (job.config.selected_indicators as string[])?.join(", ") || "—"],
                    ["news_query_mode", job.config.news_query_mode ?? "—"],
                    ["news_article_limit", job.config.news_article_limit ?? "—"],
                    ["news_date_from", job.config.news_date_from ?? "—"],
                    ["news_date_to", job.config.news_date_to ?? "—"],
                    ["news_recent_hours", job.config.news_recent_hours ?? "—"],
                    ["enable_news_web_agent", String(job.config.enable_news_web_agent ?? false)],
                    ["quick_think_llm", job.config.quick_think_llm],
                    ["deep_think_llm", job.config.deep_think_llm],
                    ["openai_reasoning_effort", job.config.openai_reasoning_effort ?? "—"],
                    ["llm_provider", job.config.llm_provider],
                    ["research_depth", job.config.research_depth],
                  ] as [string, unknown][]
                ).map(([k, v]) => (
                  <tr key={k} className="border-t border-zinc-800">
                    <td className="py-1 pr-4 text-zinc-600">{k}</td>
                    <td className="py-1 text-zinc-300">{String(v ?? "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {job && (
          <p className="mt-2 text-sm font-mono text-zinc-500">
            Status: <span className="text-mint">{job.status}</span> · {job.ticker} ·{" "}
            {job.trade_date}
            {job.final_signal && (
              <>
                {" "}
                · sygnał:{" "}
                <span
                  className={
                    /sell|underweight/i.test(job.final_signal)
                      ? "text-red-400"
                      : "text-mint"
                  }
                >
                  {job.final_signal}
                </span>
              </>
            )}
            {job.duration_ms != null && job.status !== "running" && (
              <> · czas: {(job.duration_ms / 1000).toFixed(1)} s</>
            )}
          </p>
        )}
      </div>

      {err && <p className="text-red-400 font-mono text-sm">{err}</p>}

      {job && progress.length > 0 && (
        <TransparencyProgress jobId={job.id} progress={progress} />
      )}

      {job?.error_message && (
        <pre className="text-red-400 whitespace-pre-wrap text-xs border border-red-900/50 rounded-lg p-4 font-mono">
          {job.error_message}
        </pre>
      )}

      {job?.result && job.status === "completed" && (
        <section className="border border-zinc-800 rounded-lg p-5 bg-zinc-950/40">
          <h2 className="text-lg font-mono text-mint mb-4">Raporty i wyniki</h2>
          <div className="space-y-2">
            {REPORT_KEYS.map(({ key, label }) => {
              const raw = job.result![key];
              const text =
                typeof raw === "string"
                  ? raw
                  : raw != null
                    ? JSON.stringify(raw).slice(0, 120_000)
                    : "";
              if (!text || text.length < 8) return null;
              const open = openReport === key;
              return (
                <div key={key} className="border border-zinc-800 rounded-md overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setOpenReport(open ? null : key)}
                    className="w-full flex justify-between items-center px-4 py-3 text-left font-mono text-sm text-zinc-200 hover:bg-zinc-900/80"
                  >
                    <span>{label}</span>
                    <span className="text-zinc-500">{open ? "▼" : "▶"}</span>
                  </button>
                  {open && (
                    <div className="border-t border-zinc-800 px-4 py-3 max-h-[480px] overflow-y-auto prose prose-invert prose-sm max-w-none font-mono text-zinc-300">
                      <ReactMarkdown>{text}</ReactMarkdown>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {decision && (
        <div className="border border-mint/30 rounded-lg p-4 bg-mint/5">
          <h2 className="text-mint text-sm font-mono mb-2">Final Trade Decision</h2>
          <div className="prose prose-invert prose-sm max-w-none font-mono text-zinc-200">
            <ReactMarkdown>{decision}</ReactMarkdown>
          </div>
        </div>
      )}

      {job && job.status === "running" && progress.length === 0 && (
        <p className="text-sm font-mono text-zinc-500">
          Oczekiwanie na pierwsze wpisy postępu… (worker musi zapisać krok — odśwież za
          chwilę.)
        </p>
      )}
    </div>
  );
}
