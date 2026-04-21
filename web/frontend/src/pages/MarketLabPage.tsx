import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import CandleChart, { type OhlcvRow } from "../charts/CandleChart";
import { MarketPreview } from "../api";

/**
 * Laboratorium rynku: OHLCV (yfinance przez backend) + prosty multi-series close.
 * Pełna „analiza fundamentalna z prawdopodobieństwami scenariuszy” wymaga osobnego modelu
 * kwantyfikacji ryzyka — tutaj świadomie nie generujemy liczb pozornie-naukowych.
 */
export default function MarketLabPage() {
  const [ticker, setTicker] = useState("MSFT");
  const [days, setDays] = useState(180);
  const [rows, setRows] = useState<OhlcvRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [compare, setCompare] = useState("");

  async function loadPrimary() {
    setErr(null);
    setBusy(true);
    try {
      const j = await MarketPreview.ohlcv(ticker.trim().toUpperCase(), days);
      setRows((j.rows as OhlcvRow[]) || []);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Błąd");
      setRows([]);
    } finally {
      setBusy(false);
    }
  }

  const [rows2, setRows2] = useState<OhlcvRow[]>([]);

  async function loadCompare() {
    const sym2 = compare.trim().toUpperCase();
    if (!sym2) return;
    setErr(null);
    setBusy(true);
    try {
      const j = await MarketPreview.ohlcv(sym2, days);
      setRows2((j.rows as OhlcvRow[]) || []);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Błąd");
      setRows2([]);
    } finally {
      setBusy(false);
    }
  }

  const overlayData = useMemo(() => {
    if (!rows.length) return [];
    const m = new Map(rows.map((r) => [r.date, r.close]));
    return rows2.length
      ? rows2.map((r) => ({
          date: r.date,
          a: m.get(r.date) ?? null,
          b: r.close,
        }))
      : rows.map((r) => ({ date: r.date, a: r.close, b: null as number | null }));
  }, [rows, rows2]);

  return (
    <div className="max-w-6xl space-y-8">
      <div>
        <h1 className="text-2xl font-mono text-mint mb-2">Analiza rynku (lab)</h1>
        <p className="text-sm text-zinc-500 font-mono max-w-3xl">
          Wykres świecowy (TradingView lightweight-charts) + nakładka wielu serii close (Recharts).
          Linie oporu / wybić rysuje się narzędziami analitycznymi lub ręcznymi poziomami — można
          rozszerzyć o pluginy primitive w lightweight-charts. Moduł nie zastępuje doradztwa
          inwestycyjnego.
        </p>
      </div>
      <div className="flex flex-wrap gap-3 items-end">
        <label className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500 font-mono">Ticker</span>
          <input
            className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm w-36"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500 font-mono">Dni OHLCV</span>
          <input
            type="number"
            min={30}
            max={800}
            className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm w-28"
            value={days}
            onChange={(e) => setDays(Number(e.target.value) || 180)}
          />
        </label>
        <button
          type="button"
          disabled={busy}
          onClick={loadPrimary}
          className="rounded-md bg-mint px-5 py-2 text-sm font-semibold text-black disabled:opacity-50"
        >
          Załaduj OHLCV
        </button>
        <label className="flex flex-col gap-1 min-w-[120px]">
          <span className="text-xs text-zinc-500 font-mono">Drugi ticker (close)</span>
          <input
            className="rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm"
            placeholder="np. AAPL"
            value={compare}
            onChange={(e) => setCompare(e.target.value)}
          />
        </label>
        <button
          type="button"
          disabled={busy || !compare.trim()}
          onClick={loadCompare}
          className="rounded-md border border-zinc-600 px-4 py-2 text-sm font-mono text-zinc-200 disabled:opacity-50"
        >
          Załaduj porównanie
        </button>
      </div>
      {err && <p className="text-sm text-red-400 font-mono">{err}</p>}
      {rows.length > 0 && (
        <>
          <CandleChart rows={rows} />
          <div className="h-80 w-full">
            <h2 className="text-sm font-mono text-zinc-400 mb-2">
              Zamknięcia {ticker.toUpperCase()}
              {rows2.length ? ` vs ${compare.toUpperCase()}` : ""}
            </h2>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={overlayData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 9 }} minTickGap={24} />
                <YAxis tick={{ fill: "#71717a", fontSize: 10 }} domain={["auto", "auto"]} />
                <Tooltip
                  contentStyle={{ background: "#18181b", border: "1px solid #3f3f46" }}
                />
                <Legend />
                <Line type="monotone" dataKey="a" name={ticker.toUpperCase()} stroke="#4ade80" dot={false} strokeWidth={1.5} />
                {rows2.length > 0 && (
                  <Line type="monotone" dataKey="b" name={compare.toUpperCase()} stroke="#60a5fa" dot={false} strokeWidth={1.5} />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
      <section className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-4 text-xs font-mono text-amber-100/90 space-y-2">
        <h3 className="text-sm text-amber-200">Profesjonalna analiza i prawdopodobieństwa</h3>
        <p>
          Aby spełnić wymogi profesjonalnego inwestora, scenariusze i prawdopodobieństwa muszą wynikać
          z jawnego modelu (np. symulacja Monte Carlo na zwrotach, kalibracja na historii, pełny
          opis założeń). Ten panel dostarcza infrastruktury danych i wykresów; warstwa prognozy nie
          jest tutaj automatycznie generowana, żeby uniknąć pozornie precyzyjnych liczb bez modelu.
        </p>
      </section>
    </div>
  );
}
