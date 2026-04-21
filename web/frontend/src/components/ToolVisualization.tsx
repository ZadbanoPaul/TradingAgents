import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  Brush,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ProgressRow } from "../types/progress";

const PALETTE = ["#34d399", "#38bdf8", "#fbbf24", "#f472b6", "#a78bfa", "#fb923c"];

export type ChartSetLine = {
  kind: "line";
  title: string;
  xKey: string;
  yKeys: string[];
  rows: Record<string, unknown>[];
};

export type ChartSetBar = {
  kind: "bar";
  title: string;
  bars: { name: string; value: number }[];
};

export type ChartSetArticles = {
  kind: "articles";
  title: string;
  articles: Record<string, string>[];
};

export type ChartSet = ChartSetLine | ChartSetBar | ChartSetArticles;

export type ChartHint = {
  chart_sets?: ChartSet[];
  tables?: { headers: string[]; rows: string[][] }[];
  series?: { x?: string; y?: number }[];
};

function numStats(rows: Record<string, unknown>[], key: string) {
  const nums = rows
    .map((r) => Number(r[key]))
    .filter((n) => typeof n === "number" && !Number.isNaN(n));
  if (!nums.length) return null;
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const avg = nums.reduce((a, b) => a + b, 0) / nums.length;
  return { min, max, avg, n: nums.length };
}

function LineSetChart({ set }: { set: ChartSetLine }) {
  const data = set.rows;
  const primary = set.yKeys[0] ?? "";
  const [brush, setBrush] = useState<{ startIndex?: number; endIndex?: number }>({});

  const visibleRows = useMemo(() => {
    const s = brush.startIndex ?? 0;
    const e = brush.endIndex != null ? brush.endIndex : Math.max(0, data.length - 1);
    return data.slice(s, e + 1);
  }, [data, brush]);

  const stats = primary ? numStats(visibleRows, primary) : null;

  return (
    <div className="mt-3 space-y-2 border border-zinc-800 rounded-lg p-3 bg-black/20">
      <p className="text-xs font-mono text-mint">{set.title}</p>
      <div className="h-[min(360px,55vh)] w-full min-h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
            <XAxis
              dataKey={set.xKey}
              tick={{ fill: "#a1a1aa", fontSize: 9 }}
              interval="preserveStartEnd"
              height={48}
              angle={-20}
              textAnchor="end"
            />
            <YAxis tick={{ fill: "#a1a1aa", fontSize: 10 }} domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={{
                background: "#09090b",
                border: "1px solid #3f3f46",
                fontSize: 11,
                maxWidth: 360,
              }}
              formatter={(value: number, name: string) => [value, name]}
              labelFormatter={(l) => String(l)}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {set.yKeys.map((yk, i) => (
              <Line
                key={yk}
                type="monotone"
                dataKey={yk}
                name={yk}
                stroke={PALETTE[i % PALETTE.length]}
                strokeWidth={2}
                dot={{ r: 2 }}
                activeDot={{ r: 5 }}
                isAnimationActive={false}
              />
            ))}
            {stats && <ReferenceLine y={stats.avg} stroke="#f472b6" strokeDasharray="5 5" label={{ value: "μ", fill: "#f472b6", fontSize: 10 }} />}
            <Brush
              dataKey={set.xKey}
              height={22}
              stroke="#52525b"
              fill="#18181b"
              travellerWidth={8}
              onChange={(e) => {
                if (e && typeof e === "object" && "startIndex" in e) {
                  setBrush({
                    startIndex: (e as { startIndex?: number }).startIndex,
                    endIndex: (e as { endIndex?: number }).endIndex,
                  });
                }
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {stats && primary && (
        <p className="text-[11px] font-mono text-zinc-500">
          Widoczny zakres (szczotka): <span className="text-zinc-300">{primary}</span> — min{" "}
          <span className="text-zinc-300">{stats.min.toFixed(4)}</span>, max{" "}
          <span className="text-zinc-300">{stats.max.toFixed(4)}</span>, średnia{" "}
          <span className="text-zinc-300">{stats.avg.toFixed(4)}</span> (n={stats.n})
        </p>
      )}
    </div>
  );
}

function BarSetChart({ set }: { set: ChartSetBar }) {
  const data = set.bars.map((b) => ({ ...b, name: b.name.length > 40 ? `${b.name.slice(0, 40)}…` : b.name }));
  return (
    <div className="mt-3 space-y-2 border border-zinc-800 rounded-lg p-3 bg-black/20">
      <p className="text-xs font-mono text-mint">{set.title}</p>
      <div className="h-64 w-full min-w-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 64 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
            <XAxis dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 9 }} interval={0} angle={-25} textAnchor="end" height={70} />
            <YAxis tick={{ fill: "#a1a1aa", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: "#09090b", border: "1px solid #3f3f46", fontSize: 11 }}
              formatter={(v: number) => [v, "wartość"]}
            />
            <Bar dataKey="value" fill="#34d399" radius={[4, 4, 0, 0]} name="Wartość" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ArticlesBlock({ set }: { set: ChartSetArticles }) {
  return (
    <div className="mt-3 border border-zinc-800 rounded-lg p-3 bg-black/20">
      <p className="text-xs font-mono text-mint mb-2">{set.title}</p>
      <ul className="space-y-2 text-xs text-zinc-400 max-h-64 overflow-y-auto">
        {set.articles.map((a, i) => (
          <li key={i} className="border-t border-zinc-800 pt-2 first:border-0 first:pt-0">
            <p className="text-zinc-200 font-mono">{a.title}</p>
            <p className="text-zinc-500">{a.publisher}</p>
            {a.link && (
              <a href={a.link} className="text-mint hover:underline break-all" target="_blank" rel="noreferrer">
                {a.link}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function LegacySeries({ series }: { series: { x?: string; y?: number }[] }) {
  const rows: Record<string, unknown>[] = series.map((s, i) => ({
    x: s.x ?? String(i),
    y: s.y ?? 0,
  }));
  if (!rows.length) return null;
  const set: ChartSetLine = {
    kind: "line",
    title: "Seria (legacy CSV)",
    xKey: "x",
    yKeys: ["y"],
    rows,
  };
  return <LineSetChart set={set} />;
}

export function ChartHintPanel({ hint }: { hint: ChartHint | undefined | null }) {
  if (!hint) return null;
  const sets = (hint.chart_sets ?? []) as ChartSet[];
  const tables = hint.tables ?? [];
  const legacy = hint.series ?? [];

  return (
    <div className="space-y-4">
      {sets.map((s, idx) => {
        if (s.kind === "line") return <LineSetChart key={idx} set={s} />;
        if (s.kind === "bar") return <BarSetChart key={idx} set={s} />;
        if (s.kind === "articles") return <ArticlesBlock key={idx} set={s} />;
        return null;
      })}
      {legacy.length > 0 && !sets.some((s) => s.kind === "line") && <LegacySeries series={legacy} />}
      {tables.map((tb, ti) => (
        <div key={`tb-${ti}`} className="mt-2 overflow-x-auto border border-zinc-800 rounded-md max-h-56 overflow-y-auto">
          <table className="w-full text-left text-xs font-mono text-zinc-300">
            <thead className="sticky top-0 bg-zinc-900 text-zinc-500">
              <tr>
                {tb.headers.map((h, i) => (
                  <th key={i} className="p-2 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tb.rows.map((r, ri) => (
                <tr key={ri} className="border-t border-zinc-800">
                  {r.map((c, ci) => (
                    <td key={ci} className="p-2 whitespace-pre-wrap max-w-xs">
                      {c}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

export function extractChartSetsFromProgress(progress: ProgressRow[]): ChartSet[] {
  const out: ChartSet[] = [];
  for (const p of progress) {
    if (p.type !== "tool" || p.subtype !== "result") continue;
    const h = p.chart_hint as ChartHint | undefined;
    const sets = h?.chart_sets ?? [];
    for (const s of sets) out.push(s);
  }
  return out;
}

/** Tabele z narzędzi (np. sprawozdania finansowe JSON → wiersze). */
export function extractTablesFromProgress(
  progress: ProgressRow[]
): { headers: string[]; rows: string[][] }[] {
  const out: { headers: string[]; rows: string[][] }[] = [];
  for (const p of progress) {
    if (p.type !== "tool" || p.subtype !== "result") continue;
    const h = p.chart_hint as ChartHint | undefined;
    for (const t of h?.tables ?? []) out.push(t);
  }
  return out;
}

export function LlmTotalsFooter({ progress }: { progress: ProgressRow[] }) {
  let tin = 0;
  let tout = 0;
  let tt = 0;
  let usd = 0;
  let n = 0;
  for (const p of progress) {
    if (p.type !== "llm" || p.subtype !== "response") continue;
    const u = p.usage as { input_tokens?: number; output_tokens?: number; total_tokens?: number } | undefined;
    tin += u?.input_tokens ?? 0;
    tout += u?.output_tokens ?? 0;
    tt += u?.total_tokens ?? (u?.input_tokens ?? 0) + (u?.output_tokens ?? 0);
    if (typeof p.estimated_usd === "number") {
      usd += p.estimated_usd;
      n += 1;
    }
  }
  if (!tin && !tout) return null;
  return (
    <div className="mt-8 border border-zinc-700 rounded-lg p-4 bg-zinc-900/40">
      <h3 className="text-sm font-mono text-zinc-400 mb-2">Podsumowanie tokenów LLM (bez wykresów)</h3>
      <table className="w-full text-xs font-mono text-left max-w-lg">
        <thead className="text-zinc-500">
          <tr>
            <th className="py-1 pr-4">Wejście</th>
            <th className="py-1 pr-4">Wyjście</th>
            <th className="py-1 pr-4">Razem (suma zdarzeń)</th>
            <th className="py-1">Szac. USD (suma)</th>
          </tr>
        </thead>
        <tbody>
          <tr className="text-zinc-200 border-t border-zinc-800">
            <td className="py-2">{tin}</td>
            <td className="py-2">{tout}</td>
            <td className="py-2">{tt}</td>
            <td className="py-2 text-mint">~${usd.toFixed(6)}</td>
          </tr>
        </tbody>
      </table>
      <p className="text-[11px] text-zinc-600 mt-2">
        Liczba odpowiedzi LLM z metadanymi: {n}. Koszt to suma estymacji per request (stawki przybliżone).
      </p>
    </div>
  );
}
