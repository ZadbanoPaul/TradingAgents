import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DataCatalog } from "../api";

export default function DataCatalogPage() {
  const [series, setSeries] = useState<
    { function: string; label: string; nominal_refresh: string; ttl_seconds: number }[]
  >([]);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    Promise.all([DataCatalog.avSeries(), DataCatalog.avCacheStats()])
      .then(([s, st]) => {
        if (!alive) return;
        setSeries(s.series as typeof series);
        setStats(st);
      })
      .catch((e) => {
        if (alive) setErr(e instanceof Error ? e.message : "Błąd");
      });
    return () => {
      alive = false;
    };
  }, []);

  const chartData = series.map((r) => ({
    name: String(r.function).slice(0, 14),
    ttl_h: Math.round(Number(r.ttl_seconds) / 3600),
    label: r.label,
  }));

  return (
    <div className="max-w-6xl space-y-8">
      <div>
        <h1 className="text-2xl font-mono text-mint mb-2">Katalog danych Alpha Vantage</h1>
        <p className="text-sm text-zinc-500 font-mono">
          Serie używane w backendzie + nominalny opis odświeżania i TTL cache HTTP (bez ponownego
          pobierania w oknie TTL — patrz{" "}
          <code className="text-zinc-400">tradingagents/dataflows/av_http_cache.py</code>). Pełna
          lista endpointów:{" "}
          <a
            className="text-mint underline"
            href="https://www.alphavantage.co/documentation/"
            target="_blank"
            rel="noreferrer"
          >
            dokumentacja Alpha Vantage
          </a>
          .
        </p>
      </div>
      {err && <p className="text-sm text-red-400 font-mono">{err}</p>}
      {stats && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-4 font-mono text-xs text-zinc-400 space-y-1">
          <div>
            Katalog cache: <span className="text-zinc-200">{String(stats.cache_dir)}</span>
          </div>
          <div>
            Pliki body/meta: {String(stats.body_files)} / {String(stats.meta_files)}
          </div>
          {stats.newest_cached_response_at && (
            <div>
              Ostatni zapis odpowiedzi:{" "}
              <span className="text-zinc-200">{String(stats.newest_cached_response_at)}</span> UTC
            </div>
          )}
          <div className="text-zinc-500 pt-2">{String(stats.note)}</div>
        </div>
      )}
      <div className="h-72 w-full">
        <h2 className="text-sm font-mono text-zinc-400 mb-2">TTL cache (godziny)</h2>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="name" tick={{ fill: "#71717a", fontSize: 10 }} />
            <YAxis tick={{ fill: "#71717a", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: "#18181b", border: "1px solid #3f3f46" }}
              formatter={(value: number, _n, p) => [`${value} h`, "TTL"]}
              labelFormatter={(_, p) => p?.payload?.label ?? ""}
            />
            <Bar dataKey="ttl_h" fill="#4ade80" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto rounded-lg border border-zinc-800">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-zinc-900 text-zinc-500">
            <tr>
              <th className="p-3">function</th>
              <th className="p-3">label</th>
              <th className="p-3">nominal_refresh</th>
              <th className="p-3">ttl_seconds</th>
            </tr>
          </thead>
          <tbody>
            {series.map((r) => (
              <tr key={r.function} className="border-t border-zinc-800 text-zinc-300">
                <td className="p-3 text-mint">{r.function}</td>
                <td className="p-3">{r.label}</td>
                <td className="p-3 text-zinc-500">{r.nominal_refresh}</td>
                <td className="p-3">{r.ttl_seconds}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
