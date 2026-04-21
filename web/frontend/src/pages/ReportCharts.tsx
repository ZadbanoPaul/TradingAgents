import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Jobs, type JobDetail } from "../api";
import {
  ChartHintPanel,
  extractChartSetsFromProgress,
  extractTablesFromProgress,
} from "../components/ToolVisualization";
import type { ProgressRow } from "../types/progress";

/** Załącznik analityczny: wszystkie zbiory wykresów z narzędzi get_* dla ukończonego raportu. */
export default function ReportCharts() {
  const { id } = useParams();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    const j = await Jobs.get(Number(id));
    setJob(j);
  }, [id]);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        await load();
      } catch (e) {
        if (!c) setErr(e instanceof Error ? e.message : "Błąd");
      }
    })();
    return () => {
      c = true;
    };
  }, [load]);

  const progress = (job?.progress ?? []) as ProgressRow[];
  const sets = extractChartSetsFromProgress(progress);
  const extraTables = extractTablesFromProgress(progress);

  return (
    <div className="max-w-6xl space-y-8 pb-16">
      <Link to={id ? `/live/${id}` : "/history"} className="text-sm font-mono text-mint hover:underline">
        ← Powrót do raportu #{id}
      </Link>
      <div>
        <h1 className="text-2xl font-mono text-mint">Analizy i wykresy (załącznik)</h1>
        {job && (
          <p className="mt-2 text-sm font-mono text-zinc-500">
            {job.ticker} · {job.trade_date} · status: {job.status}
          </p>
        )}
      </div>
      {err && <p className="text-red-400 font-mono text-sm">{err}</p>}
      {job?.status !== "completed" && job?.status !== "failed" && (
        <p className="text-zinc-500 font-mono text-sm">
          Raport w toku — wykresy uzupełniają się po wywołaniach narzędzi. Odśwież stronę za chwilę.
        </p>
      )}
      {sets.length === 0 && job?.status === "completed" && (
        <p className="text-zinc-500 font-mono text-sm">
          Brak danych do wykresów (brak zdarzeń narzędzi z JSON w postępie). Uruchom nową analizę po
          aktualizacji narzędzi.
        </p>
      )}
      {sets.length > 0 && (
        <section className="space-y-8 border border-zinc-800 rounded-lg p-6 bg-zinc-950/50">
          <p className="text-xs text-zinc-500 font-mono">
            Interaktywne wykresy: szczotka (Brush) zmienia zakres; linia przerywana — średnia arytmetyczna
            pierwszej serii w widocznym oknie; aktywne punkty (Tooltip) pokazują wartości.
          </p>
          {sets.map((s, i) => (
            <div key={i} className="border-t border-zinc-800 pt-6 first:border-0 first:pt-0">
              <ChartHintPanel hint={{ chart_sets: [s], tables: [], series: [] }} />
            </div>
          ))}
        </section>
      )}
      {extraTables.length > 0 && (
        <section className="border border-zinc-800 rounded-lg p-6 bg-zinc-950/50">
          <h2 className="text-sm font-mono text-mint mb-3">Tabele (fundamenty / metryki z narzędzi)</h2>
          <ChartHintPanel hint={{ chart_sets: [], tables: extraTables, series: [] }} />
        </section>
      )}
    </div>
  );
}
