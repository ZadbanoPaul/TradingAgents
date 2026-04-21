import { useState } from "react";
import { Link } from "react-router-dom";
import { Screen, type CandidateRow } from "../api";

export default function Candidates() {
  const [lookback, setLookback] = useState(90);
  const [maxTickers, setMaxTickers] = useState(30);
  const [tickersRaw, setTickersRaw] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [rows, setRows] = useState<CandidateRow[]>([]);
  const [note, setNote] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  async function run() {
    setBusy(true);
    setErr(null);
    try {
      const tickers = tickersRaw
        .split(/[\s,;]+/)
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean);
      const res = await Screen.candidates({
        tickers: tickers.length ? tickers : null,
        lookback_days: lookback,
        max_tickers: maxTickers,
      });
      setRows(res.rows);
      setNote(res.universe_note);
      setErrors(res.errors || []);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Błąd");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-6xl space-y-6 pb-16">
      <Link to="/" className="text-sm font-mono text-mint hover:underline">
        ← Overview
      </Link>
      <h1 className="text-2xl font-mono text-mint">Kandydaci (szybki skan)</h1>
      <p className="text-xs text-zinc-500 font-mono max-w-3xl">
        Uproszczona analiza OHLC (yfinance): przecena od szczytu okresu, pozycja w widełkach high–low, odchylenie od
        średniej zamknięć, prosty score. Domyślnie zestaw dużych spółek US — wklej własne tickery, aby ograniczyć
        uniwersum. Pełne pokrycie rynku USA wymaga własnego feedu tickerów.
      </p>

      <div className="border border-zinc-800 rounded-lg p-5 bg-zinc-950/50 space-y-4 font-mono text-sm">
        <label className="flex flex-col gap-1 max-w-xs">
          <span className="text-xs text-zinc-500">Lookback (dni)</span>
          <input
            type="number"
            min={5}
            max={365}
            className="rounded border border-zinc-700 bg-black/40 px-2 py-1"
            value={lookback}
            onChange={(e) => setLookback(Number(e.target.value) || 90)}
          />
        </label>
        <label className="flex flex-col gap-1 max-w-xs">
          <span className="text-xs text-zinc-500">Max tickerów na zapytanie</span>
          <input
            type="number"
            min={1}
            max={80}
            className="rounded border border-zinc-700 bg-black/40 px-2 py-1"
            value={maxTickers}
            onChange={(e) => setMaxTickers(Number(e.target.value) || 30)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500">Tickery (opcjonalnie, spacja/przecinek)</span>
          <textarea
            className="rounded border border-zinc-700 bg-black/40 px-2 py-2 min-h-[72px] text-xs"
            placeholder="np. AAPL MSFT CRM …"
            value={tickersRaw}
            onChange={(e) => setTickersRaw(e.target.value)}
          />
        </label>
        <button
          type="button"
          disabled={busy}
          onClick={() => void run()}
          className="rounded bg-mint px-4 py-2 text-black font-semibold disabled:opacity-50"
        >
          {busy ? "Skanowanie…" : "Uruchom skan"}
        </button>
        {err && <p className="text-red-400 text-xs">{err}</p>}
      </div>

      {note && <p className="text-xs text-zinc-500 font-mono border border-zinc-800 rounded p-3">{note}</p>}

      {errors.length > 0 && (
        <div className="text-xs text-amber-400 font-mono border border-amber-900/40 rounded p-3">
          <p className="text-mint mb-1">Ostrzeżenia / pominięcia</p>
          <ul className="list-disc pl-4 space-y-1">
            {errors.slice(0, 20).map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      )}

      {rows.length > 0 && (
        <div className="overflow-x-auto border border-zinc-800 rounded-lg">
          <table className="w-full text-left text-xs font-mono text-zinc-300">
            <thead className="bg-zinc-900 text-zinc-500">
              <tr>
                <th className="p-2">Ticker</th>
                <th className="p-2">Close</th>
                <th className="p-2">High okresu</th>
                <th className="p-2">Low</th>
                <th className="p-2">Śr. close</th>
                <th className="p-2">Δ od high %</th>
                <th className="p-2">vs śr. %</th>
                <th className="p-2">Pozycja w range</th>
                <th className="p-2">Mcap</th>
                <th className="p-2">Score</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-t border-zinc-800">
                  <td className="p-2 text-mint">{String(r.ticker)}</td>
                  <td className="p-2">{String(r.close)}</td>
                  <td className="p-2">{String(r.period_high)}</td>
                  <td className="p-2">{String(r.period_low)}</td>
                  <td className="p-2">{String(r.period_avg_close)}</td>
                  <td className="p-2">{r.decline_from_period_high_pct != null ? String(r.decline_from_period_high_pct) : "—"}</td>
                  <td className="p-2">{r.vs_period_avg_pct != null ? String(r.vs_period_avg_pct) : "—"}</td>
                  <td className="p-2">{r.position_in_range_0_1 != null ? String(r.position_in_range_0_1) : "—"}</td>
                  <td className="p-2">{r.market_cap != null ? String(r.market_cap) : "—"}</td>
                  <td className="p-2 text-mint">{String(r.signal_score)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
