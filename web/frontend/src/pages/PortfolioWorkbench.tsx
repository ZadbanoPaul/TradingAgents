import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Insights, Jobs, type CompletedJobRow } from "../api";

export default function PortfolioWorkbench() {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [jobs, setJobs] = useState<CompletedJobRow[]>([]);
  const [sel, setSel] = useState<Record<number, boolean>>({});
  const [notional, setNotional] = useState(100_000);
  const [slots, setSlots] = useState(8);
  const [minute, setMinute] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, unknown> | null>(null);
  const [synthJobId, setSynthJobId] = useState<number | null>(null);

  async function loadJobs() {
    setBusy(true);
    setErr(null);
    try {
      const r = await Insights.completedJobs({
        date_from: from || undefined,
        date_to: to || undefined,
        limit: 200,
      });
      setJobs(r.jobs);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Błąd");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void loadJobs();
  }, []);

  const selectedIds = useMemo(
    () => jobs.filter((j) => sel[j.id]).map((j) => j.id),
    [jobs, sel]
  );

  async function buildDraft() {
    if (!selectedIds.length) {
      setErr("Zaznacz co najmniej jeden zakończony job.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      const r = await Insights.portfolioDraft({
        job_ids: selectedIds,
        notional_usd: notional,
        num_positions: slots,
        include_minute_last_day: minute,
      });
      setDraft(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Błąd");
    } finally {
      setBusy(false);
    }
  }

  async function queuePortfolioSynthesis() {
    if (!selectedIds.length) {
      setErr("Zaznacz co najmniej jeden zakończony job.");
      return;
    }
    setBusy(true);
    setErr(null);
    setSynthJobId(null);
    try {
      const j = await Jobs.createPortfolioSynthesis({
        source_job_ids: selectedIds,
        notional_usd: notional,
        num_positions: slots,
        include_minute_last_day: minute,
        report_language: "pl",
      });
      setSynthJobId(j.id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Błąd");
    } finally {
      setBusy(false);
    }
  }

  const md = typeof draft?.markdown_table === "string" ? draft.markdown_table : "";

  return (
    <div className="max-w-6xl space-y-6 pb-16">
      <Link to="/" className="text-sm font-mono text-mint hover:underline">
        ← Overview
      </Link>
      <h1 className="text-2xl font-mono text-mint">Portfel (z historii analiz)</h1>
      <p className="text-xs text-zinc-500 font-mono max-w-3xl">
        Wybierz zakończone joby w oknie dat, zaznacz tickery, podaj kapitał i liczbę slotów. Backend buduje szkic
        alokacji (wagi po sygnałach) oraz opcjonalnie próbkę świec 1m (ostatni dzień) dla pierwszych walorów —
        limity yfinance.         Przycisk poniżej kolejkuje job <code className="text-zinc-400">portfolio_synthesis</code> (jeden przebieg LLM
        „deep” na skróconych sekcjach raportów wybranych jobów + szkic wag).
      </p>

      <div className="flex flex-wrap gap-3 items-end border border-zinc-800 rounded-lg p-4 bg-zinc-950/50 font-mono text-xs">
        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">Od (YYYY-MM-DD)</span>
          <input
            type="date"
            className="rounded border border-zinc-700 bg-black/40 px-2 py-1"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">Do</span>
          <input
            type="date"
            className="rounded border border-zinc-700 bg-black/40 px-2 py-1"
            value={to}
            onChange={(e) => setTo(e.target.value)}
          />
        </label>
        <button
          type="button"
          disabled={busy}
          onClick={() => void loadJobs()}
          className="rounded border border-mint/40 px-3 py-2 text-mint hover:bg-mint/10"
        >
          Odśwież listę
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="border border-zinc-800 rounded-lg overflow-hidden max-h-[480px] overflow-y-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-zinc-900 text-zinc-500 sticky top-0">
              <tr>
                <th className="p-2 w-10">✓</th>
                <th className="p-2">ID</th>
                <th className="p-2">Ticker</th>
                <th className="p-2">Data</th>
                <th className="p-2">Sygnał</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id} className="border-t border-zinc-800">
                  <td className="p-2">
                    <input
                      type="checkbox"
                      checked={!!sel[j.id]}
                      onChange={(e) => setSel((s) => ({ ...s, [j.id]: e.target.checked }))}
                    />
                  </td>
                  <td className="p-2 text-zinc-500">{j.id}</td>
                  <td className="p-2 text-mint">{j.ticker}</td>
                  <td className="p-2">{j.trade_date}</td>
                  <td className="p-2">{j.final_signal || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-3 border border-zinc-800 rounded-lg p-4 font-mono text-xs">
          <label className="flex flex-col gap-1">
            <span className="text-zinc-500">Kapitał (USD)</span>
            <input
              type="number"
              className="rounded border border-zinc-700 bg-black/40 px-2 py-1"
              value={notional}
              min={1000}
              onChange={(e) => setNotional(Number(e.target.value) || 0)}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-zinc-500">Liczba pozycji (max)</span>
            <input
              type="number"
              className="rounded border border-zinc-700 bg-black/40 px-2 py-1"
              value={slots}
              min={1}
              max={32}
              onChange={(e) => setSlots(Number(e.target.value) || 1)}
            />
          </label>
          <label className="flex items-center gap-2 text-zinc-300 cursor-pointer">
            <input type="checkbox" checked={minute} onChange={(e) => setMinute(e.target.checked)} />
            Świece 1m (ostatni dzień, pierwsze walory — eksperymentalne)
          </label>
          <button
            type="button"
            disabled={busy}
            onClick={() => void buildDraft()}
            className="rounded bg-mint px-4 py-2 text-black font-semibold disabled:opacity-50"
          >
            Zbuduj szkic portfela
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void queuePortfolioSynthesis()}
            className="rounded border border-mint/50 px-4 py-2 text-mint hover:bg-mint/10 disabled:opacity-50"
          >
            Zleć syntezę LLM (job w tle)
          </button>
          {synthJobId != null && (
            <p className="text-zinc-400">
              Utworzono job{" "}
              <Link className="text-mint underline" to={`/live/${synthJobId}`}>
                #{synthJobId}
              </Link>
              .
            </p>
          )}
          {err && <p className="text-red-400">{err}</p>}
        </div>
      </div>

      {draft && (
        <section className="border border-zinc-800 rounded-lg p-4 space-y-3 font-mono text-xs text-zinc-300">
          <h2 className="text-mint text-sm">Wynik</h2>
          {typeof draft.note === "string" && <p className="text-zinc-500">{draft.note}</p>}
          <pre className="whitespace-pre-wrap text-zinc-400 border border-zinc-800 rounded p-3 overflow-x-auto">
            {md}
          </pre>
        </section>
      )}
    </div>
  );
}
