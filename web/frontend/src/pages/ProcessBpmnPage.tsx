import { useEffect, useMemo, useRef, useState } from "react";
import { DEEP_CORE, MEDIUM_CORE, SHALLOW_CORE } from "./processBpmnDiagrams";

type Depth = "shallow" | "medium" | "deep";

const DEPTH_LABEL: Record<Depth, string> = {
  shallow: "Shallow — krótsze pętle debaty i ryzyka (max = 1 w UI)",
  medium: "Medium — średnie pętle (max = 2)",
  deep: "Deep — najdłuższe pętle (max = 3)",
};

export default function ProcessBpmnPage() {
  const [depth, setDepth] = useState<Depth>("medium");
  const hostRef = useRef<HTMLDivElement>(null);
  const diagram = useMemo(() => {
    if (depth === "shallow") return SHALLOW_CORE;
    if (depth === "medium") return MEDIUM_CORE;
    return DEEP_CORE;
  }, [depth]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let cancelled = false;

    (async () => {
      const mermaid = (await import("mermaid")).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        securityLevel: "loose",
        fontFamily: "ui-monospace, monospace",
      });
      if (cancelled) return;
      host.innerHTML = `<div class="mermaid">${diagram}</div>`;
      await mermaid.run({ nodes: host.querySelectorAll<HTMLElement>(".mermaid") });
    })();

    return () => {
      cancelled = true;
    };
  }, [diagram]);

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-mono text-mint mb-2">Proces agentów (graf)</h1>
        <p className="text-sm text-zinc-500 font-mono max-w-3xl">
          Wizualizacja przepływu zgodna z{" "}
          <code className="text-zinc-400">tradingagents/graph/setup.py</code>. Dokładny opis BPMN,
          pamięci BM25 i cache AV: repozytorium{" "}
          <span className="text-zinc-400">docs/agents-process-bpmn-and-memory.md</span>.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {(["shallow", "medium", "deep"] as const).map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => setDepth(d)}
            className={`rounded-md px-4 py-2 text-xs font-mono border ${
              depth === d
                ? "border-mint bg-mint/10 text-mint"
                : "border-zinc-700 text-zinc-400 hover:border-zinc-500"
            }`}
          >
            {DEPTH_LABEL[d]}
          </button>
        ))}
      </div>
      <div
        ref={hostRef}
        className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4 overflow-x-auto"
      />
    </div>
  );
}
