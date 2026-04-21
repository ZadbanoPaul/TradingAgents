import { useCallback, useState } from "react";
import { ChartHintPanel, LlmTotalsFooter, type ChartHint } from "./ToolVisualization";
import type { ProgressRow } from "../types/progress";

export type { ProgressRow };

function artifactHref(jobId: number, row: ProgressRow): string | null {
  const art = row.artifact;
  if (typeof art !== "string" || !art) return null;
  const basePath =
    typeof row.artifact_download_path === "string"
      ? row.artifact_download_path
      : `/api/jobs/${jobId}/artifacts/download`;
  return `${basePath}?relpath=${encodeURIComponent(art)}`;
}

type MsgSummary = {
  role?: string;
  chars?: number;
  blocks?: number;
  sha256?: string;
  preview?: string;
};

function ExpandableScrollText({
  text,
  className = "",
}: {
  text: string;
  className?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`mt-2 space-y-2 ${className}`}>
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="text-[11px] font-mono rounded border border-zinc-700 px-2 py-1 text-mint hover:bg-zinc-800"
      >
        {expanded ? "Zwiń okno" : "Rozwiń okno"}
      </button>
      <pre
        className={`text-xs text-zinc-400 whitespace-pre-wrap break-words border border-zinc-800 rounded p-2 bg-black/30 overflow-y-auto overflow-x-auto ${
          expanded ? "max-h-[min(88vh,1400px)] min-h-[160px]" : "max-h-48"
        }`}
      >
        {text}
      </pre>
    </div>
  );
}

function MessagesTable({
  rows,
  requestArtifactUrl,
}: {
  rows: MsgSummary[];
  /** Pełny URL do artefaktu llm_request (JSON z messages_full). */
  requestArtifactUrl?: string | null;
}) {
  const [expandedRow, setExpandedRow] = useState<Record<number, boolean>>({});
  const [fullContents, setFullContents] = useState<string[] | null>(null);
  const [artifactLoading, setArtifactLoading] = useState(false);
  const [artifactErr, setArtifactErr] = useState<string | null>(null);

  const loadFullFromArtifact = useCallback(async () => {
    if (!requestArtifactUrl) return;
    setArtifactLoading(true);
    setArtifactErr(null);
    try {
      const r = await fetch(requestArtifactUrl, { credentials: "include" });
      if (!r.ok) {
        throw new Error((await r.text()) || r.statusText);
      }
      const j = (await r.json()) as { messages_full?: { content?: string }[] };
      const arr = Array.isArray(j.messages_full) ? j.messages_full : [];
      setFullContents(arr.map((m) => String(m?.content ?? "")));
    } catch (e) {
      setArtifactErr(e instanceof Error ? e.message : "Błąd wczytywania");
      setFullContents(null);
    } finally {
      setArtifactLoading(false);
    }
  }, [requestArtifactUrl]);

  if (!rows.length) return null;
  return (
    <div className="mt-3 space-y-2">
      {requestArtifactUrl && (
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={artifactLoading}
            onClick={() => void loadFullFromArtifact()}
            className="text-[11px] font-mono rounded border border-mint/40 px-2 py-1 text-mint hover:bg-mint/10 disabled:opacity-50"
          >
            {artifactLoading ? "Wczytywanie…" : fullContents ? "Załaduj ponownie z artefaktu" : "Wczytaj pełną treść z artefaktu"}
          </button>
          <span className="text-[10px] text-zinc-600 font-mono">
            Bez limitu znaków z pliku JSON (messages_full)
          </span>
        </div>
      )}
      {artifactErr && <p className="text-[11px] text-red-400 font-mono">{artifactErr}</p>}
      <div className="overflow-x-auto border border-zinc-800 rounded-md">
        <table className="w-full text-left text-xs font-mono text-zinc-300 table-fixed">
          <thead className="bg-zinc-900 text-zinc-500">
            <tr>
              <th className="p-2 w-20">Rola</th>
              <th className="p-2 w-16">Znaki</th>
              <th className="p-2 w-14">Bloki</th>
              <th className="p-2 w-[140px]">SHA256</th>
              <th className="p-2 min-w-[280px]">Podgląd</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const expanded = !!expandedRow[i];
              const body = fullContents && fullContents[i] !== undefined ? fullContents[i] : (r.preview ?? "");
              const wasTruncatedInEvent = !!(r.preview && r.preview.endsWith("…"));
              return (
                <tr key={i} className="border-t border-zinc-800 align-top">
                  <td className="p-2 text-mint align-top">{r.role}</td>
                  <td className="p-2 align-top">{r.chars ?? "—"}</td>
                  <td className="p-2 align-top">{r.blocks ?? "—"}</td>
                  <td className="p-2 break-all text-zinc-500 align-top text-[10px]">{r.sha256 ?? "—"}</td>
                  <td className="p-2 align-top min-w-0">
                    <div className="flex flex-wrap gap-2 mb-1">
                      <button
                        type="button"
                        onClick={() => setExpandedRow((m) => ({ ...m, [i]: !m[i] }))}
                        className="text-[11px] rounded border border-zinc-700 px-2 py-0.5 text-mint hover:bg-zinc-800 shrink-0"
                      >
                        {expanded ? "Zwiń" : "Rozwiń"}
                      </button>
                    </div>
                    <div
                      className={`whitespace-pre-wrap break-words rounded border border-zinc-800/80 p-2 bg-black/40 text-zinc-400 overflow-y-auto overflow-x-auto ${
                        expanded ? "max-h-[min(88vh,1400px)] min-h-[120px]" : "max-h-40"
                      }`}
                    >
                      {body}
                    </div>
                    {wasTruncatedInEvent && !fullContents && (
                      <p className="text-[10px] text-zinc-600 mt-1 font-mono">
                        Końcówka skrócona w evencie — użyj „Wczytaj pełną treść z artefaktu”.
                      </p>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function compactOneLine(jobId: number, p: ProgressRow, i: number): string {
  const ts = typeof p.ts === "string" ? p.ts : "";
  const typ = typeof p.type === "string" ? p.type : "graph";
  const step = typeof p.step_no === "number" ? p.step_no : i + 1;
  const agent =
    typeof p.agent_label === "string" && p.agent_label
      ? p.agent_label
      : typeof p.title === "string"
        ? p.title
        : typ;
  const tail =
    typ === "llm"
      ? String((p as { model?: string }).model || "LLM")
      : typ === "tool"
        ? String((p as { tool_name?: string }).tool_name || "narzędzie")
        : "graf";
  return `#${step} · job ${jobId} · progress[${i + 1}] · ${ts} · ${agent} · ${tail}`;
}

export function TransparencyProgress({ jobId, progress }: { jobId: number; progress: ProgressRow[] }) {
  const [compact, setCompact] = useState(false);
  if (!progress.length) return null;
  return (
    <section className="border border-zinc-800 rounded-lg p-5 bg-zinc-950/60">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <h2 className="text-lg font-mono text-mint">Przebieg analizy (transparentność)</h2>
        <div className="flex flex-wrap gap-2 items-center">
          <button
            type="button"
            onClick={() => setCompact((c) => !c)}
            className="text-[11px] font-mono rounded border border-zinc-600 px-3 py-1.5 text-zinc-200 hover:bg-zinc-800"
          >
            {compact ? "Pełny widok kroków" : "Zwinięty widok (agent · czas · id postępu)"}
          </button>
        </div>
      </div>
      <p className="text-xs text-zinc-500 font-mono mb-4">
        Kroki grafu z etykietą agenta (heurystyka ze stanu LangGraph). Zwinięty widok ukrywa szczegóły LLM/narzędzi —
        zostaje skrót: numer kroku, czas, identyfikator wpisu w tablicy postępu oraz agent.
      </p>
      {compact ? (
        <ol className="space-y-2 font-mono text-[11px] text-zinc-400 border border-zinc-800 rounded-md p-3 max-h-[70vh] overflow-y-auto">
          {progress.map((p, i) => (
            <li key={`c-${i}`} className="whitespace-pre-wrap break-words border-b border-zinc-900/80 pb-2 last:border-0">
              {compactOneLine(jobId, p, i)}
            </li>
          ))}
        </ol>
      ) : null}
      {!compact ? (
      <ol className="space-y-6 border-l border-mint/30 pl-4 ml-1">
        {progress.map((p, i) => {
          const ts = typeof p.ts === "string" ? p.ts : "";
          const typ = typeof p.type === "string" ? p.type : "graph";
          if (typ === "graph" || !p.type) {
            const title = typeof p.title === "string" ? p.title : "";
            const lines = Array.isArray(p.lines) ? (p.lines as string[]) : [];
            const agent = typeof p.agent_label === "string" ? p.agent_label : "";
            return (
              <li key={`${ts}-${i}`} className="relative">
                <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-mint" />
                <p className="text-xs text-zinc-500 font-mono">{ts}</p>
                <p className="text-xs text-zinc-600 font-mono mb-1">
                  krok grafu · postęp[{i + 1}] {agent ? `· ${agent}` : ""}
                </p>
                <p className="text-sm font-mono text-mint">{title}</p>
                <ul className="mt-2 space-y-1 text-sm text-zinc-300 font-mono list-disc pl-4">
                  {lines.map((ln, j) => (
                    <li key={j} className="whitespace-pre-wrap break-words">
                      {ln}
                    </li>
                  ))}
                </ul>
              </li>
            );
          }

          if (typ === "llm") {
            const subtype = p.subtype === "response" ? "response" : "request";
            const title = typeof p.title === "string" ? p.title : "LLM";
            const model = typeof p.model === "string" ? p.model : "";
            const effort = p.openai_reasoning_effort;
            const href = artifactHref(jobId, p);
            const msgs = Array.isArray(p.messages_summary) ? (p.messages_summary as MsgSummary[]) : [];
            const usage = p.usage as { input_tokens?: number; output_tokens?: number; total_tokens?: number } | undefined;
            const usd = typeof p.estimated_usd === "number" ? p.estimated_usd : null;
            const inp = usage?.input_tokens ?? 0;
            const out = usage?.output_tokens ?? 0;
            const tot = usage?.total_tokens ?? inp + out;
            return (
              <li key={`${ts}-${i}`} className="relative">
                <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-emerald-400" />
                <p className="text-xs text-zinc-500 font-mono">{ts}</p>
                <p className="text-sm font-mono text-emerald-300">{title}</p>
                <div className="mt-2 space-y-1 text-xs font-mono text-zinc-400">
                  <p>
                    Model: <span className="text-zinc-200">{model}</span>
                    {p.model_role != null && (
                      <>
                        {" "}
                        · rola: <span className="text-zinc-200">{String(p.model_role)}</span>
                      </>
                    )}
                  </p>
                  {effort != null && String(effort) !== "" && (
                    <p>
                      Reasoning (OpenAI): <span className="text-zinc-200">{String(effort)}</span>
                    </p>
                  )}
                  {subtype === "request" && (
                    <>
                      <p>
                        Wiadomości: {String(p.message_count ?? "—")} · partie (batches):{" "}
                        {String(p.llm_message_batches ?? "—")} · suma bloków treści (chunki):{" "}
                        {String(p.content_blocks_total ?? "—")}
                      </p>
                      {typeof p.content_chunks_note === "string" && (
                        <p className="text-zinc-500">{p.content_chunks_note}</p>
                      )}
                      {typeof p.context_how_built === "string" && (
                        <p className="text-zinc-500 border-l-2 border-zinc-700 pl-2">{p.context_how_built}</p>
                      )}
                      <p>
                        Złączone znaki: {String(p.total_chars ?? "—")} · SHA256 (złączone):{" "}
                        <span className="break-all text-zinc-500">{String(p.joined_sha256 ?? "—")}</span>
                      </p>
                    </>
                  )}
                  {subtype === "response" && (
                    <div className="mt-2 overflow-x-auto border border-zinc-800 rounded-md">
                      <table className="w-full text-xs font-mono text-left">
                        <thead className="bg-zinc-900 text-zinc-500">
                          <tr>
                            <th className="p-2">Tokeny wej.</th>
                            <th className="p-2">Tokeny wyj.</th>
                            <th className="p-2">Razem</th>
                            <th className="p-2">Szac. USD (req)</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr className="border-t border-zinc-800">
                            <td className="p-2">{inp}</td>
                            <td className="p-2">{out}</td>
                            <td className="p-2">{tot}</td>
                            <td className="p-2 text-mint">{usd != null ? `~$${usd.toFixed(6)}` : "—"}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  )}
                  {href && (
                    <p className="pt-2">
                      <a
                        href={href}
                        className="text-mint hover:underline"
                        download
                        target="_blank"
                        rel="noreferrer"
                      >
                        Pobierz artefakt JSON (pełna treść)
                      </a>
                      {" · "}
                      <a href="/prompts" className="text-mint hover:underline" target="_blank" rel="noreferrer">
                        Edytor promptów
                      </a>
                    </p>
                  )}
                  {subtype === "request" && (
                    <p className="pt-1">
                      <a href="/prompts" className="text-mint hover:underline" target="_blank" rel="noreferrer">
                        Szablony promptów (kontekst systemowy z kodu / override użytkownika)
                      </a>
                    </p>
                  )}
                </div>
                {subtype === "request" && msgs.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-zinc-500 font-mono mb-1">
                      Podsumowanie wiadomości do LLM — przewijanie, rozwiń/zwiń, wczytanie pełnej treści z
                      artefaktu.
                    </p>
                    <MessagesTable rows={msgs} requestArtifactUrl={href ?? null} />
                  </div>
                )}
                {subtype === "response" && typeof p.response_preview === "string" && (
                  <ExpandableScrollText text={p.response_preview} />
                )}
              </li>
            );
          }

          if (typ === "tool") {
            const title = typeof p.title === "string" ? p.title : "Narzędzie";
            const href = artifactHref(jobId, p);
            const hint = p.chart_hint as ChartHint | undefined;
            const hasCharts = (hint?.chart_sets?.length ?? 0) > 0 || (hint?.tables?.length ?? 0) > 0;
            return (
              <li key={`${ts}-${i}`} className="relative">
                <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-amber-400" />
                <p className="text-xs text-zinc-500 font-mono">{ts}</p>
                <p className="text-sm font-mono text-amber-200">{title}</p>
                <div className="mt-2 text-xs font-mono text-zinc-400 space-y-1">
                  {p.tool_name != null && <p>Narzędzie: {String(p.tool_name)}</p>}
                  {p.input_chars != null && <p>Wejście — znaki: {String(p.input_chars)}</p>}
                  {p.output_chars != null && <p>Wyjście — znaki: {String(p.output_chars)}</p>}
                  {typeof p.input_preview === "string" && p.input_preview && (
                    <pre className="text-zinc-500 whitespace-pre-wrap break-words border border-zinc-800 rounded p-2 max-h-32 overflow-y-auto">
                      {p.input_preview}
                    </pre>
                  )}
                  {href && (
                    <p>
                      <a href={href} className="text-mint hover:underline" download target="_blank" rel="noreferrer">
                        Artefakt wej./wyj. (JSON)
                      </a>
                    </p>
                  )}
                </div>
                <ChartHintPanel hint={hint} />
                {typeof p.output_preview === "string" && p.output_preview && !hasCharts && (
                  <pre className="mt-2 text-xs text-zinc-500 whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                    {p.output_preview}
                  </pre>
                )}
              </li>
            );
          }

          return (
            <li key={`${ts}-${i}`} className="relative text-xs font-mono text-zinc-500">
              <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-zinc-600" />
              {ts} — {typ}
              <pre className="mt-1 text-zinc-600 overflow-x-auto">{JSON.stringify(p, null, 0).slice(0, 4000)}</pre>
            </li>
          );
        })}
      </ol>
      ) : null}
      <LlmTotalsFooter progress={progress} />
    </section>
  );
}
