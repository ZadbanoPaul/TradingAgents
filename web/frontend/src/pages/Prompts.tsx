import { useEffect, useState } from "react";
import {
  PromptMeta,
  Prompts as Papi,
  PromptVersions,
  type PlaceholderRow,
  type PromptItem,
  type PromptVersionSummary,
} from "../api";

export default function Prompts() {
  const [items, setItems] = useState<PromptItem[]>([]);
  const [sel, setSel] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [versions, setVersions] = useState<PromptVersionSummary[]>([]);
  const [ph, setPh] = useState<PlaceholderRow[]>([]);
  const [contractOpen, setContractOpen] = useState(false);
  const [contractJson, setContractJson] = useState("");

  const current = items.find((i) => i.key === sel);

  useEffect(() => {
    Papi.list()
      .then((list) => {
        setItems(list);
        if (list.length) {
          setSel((prev) => {
            if (prev && list.some((i) => i.key === prev)) return prev;
            return list[0].key;
          });
        }
      })
      .catch(() => setItems([]));
  }, []);

  useEffect(() => {
    PromptMeta.placeholders()
      .then((r) => setPh(r.placeholders))
      .catch(() => setPh([]));
  }, []);

  useEffect(() => {
    const it = items.find((i) => i.key === sel);
    if (it) setBody(it.current_body);
  }, [sel, items]);

  useEffect(() => {
    if (!sel) {
      setVersions([]);
      return;
    }
    PromptVersions.list(sel)
      .then(setVersions)
      .catch(() => setVersions([]));
  }, [sel, items]);

  async function save() {
    if (!sel) return;
    setMsg(null);
    try {
      await Papi.save(sel, body);
      const list = await Papi.list();
      setItems(list);
      const v = await PromptVersions.list(sel);
      setVersions(v);
      setMsg("Zapisano nową wersję promptu (numer + znacznik czasu).");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Błąd");
    }
  }

  async function reset() {
    if (!sel) return;
    setMsg(null);
    try {
      await Papi.reset(sel);
      const list = await Papi.list();
      setItems(list);
      const it = list.find((i) => i.key === sel);
      if (it) setBody(it.current_body);
      setVersions([]);
      setMsg("Usunięto wszystkie wersje i nadpisanie — przywrócono domyślny szablon z kodu.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Błąd");
    }
  }

  async function activateVersion(rowId: number) {
    setMsg(null);
    try {
      await PromptVersions.activate(rowId);
      const list = await Papi.list();
      setItems(list);
      if (sel) {
        const v = await PromptVersions.list(sel);
        setVersions(v);
        const it = list.find((i) => i.key === sel);
        if (it) setBody(it.current_body);
      }
      setMsg("Ustawiono aktywną wersję.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Błąd");
    }
  }

  async function deleteVersionRow(rowId: number, active: boolean) {
    if (active) {
      setMsg("Nie można usunąć wersji aktywnej.");
      return;
    }
    setMsg(null);
    try {
      await PromptVersions.remove(rowId);
      if (sel) setVersions(await PromptVersions.list(sel));
      setMsg("Usunięto wersję z historii.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Błąd");
    }
  }

  async function loadVersionIntoEditor(rowId: number) {
    setMsg(null);
    try {
      const row = await PromptVersions.getRow(rowId);
      setBody(row.body);
      setMsg("Wczytano treść wersji do edytora — zapis utworzy nową wersję.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Błąd");
    }
  }

  async function loadOutputContract() {
    setContractOpen(true);
    try {
      const j = await PromptMeta.outputContract();
      setContractJson(JSON.stringify(j, null, 2));
    } catch (e) {
      setContractJson(e instanceof Error ? e.message : "Błąd");
    }
  }

  return (
    <div className="max-w-6xl flex flex-col xl:flex-row gap-8">
      <div className="xl:w-72 shrink-0 space-y-2">
        <h1 className="text-2xl font-mono text-mint mb-4">Prompts</h1>
        <p className="text-xs text-zinc-500 font-mono mb-4">
          Każdy zapis tworzy nową wersję z numerem i timestampem. Aktywna wersja jest używana przez
          worker; można przywrócić starszą (aktywacja) lub usunąć nieaktywne wpisy.
        </p>
        <div className="flex flex-col gap-1 max-h-[48vh] overflow-y-auto pr-1">
          {items.map((it) => (
            <button
              key={it.key}
              type="button"
              onClick={() => setSel(it.key)}
              className={`text-left rounded-md px-3 py-2 text-xs font-mono border ${
                sel === it.key
                  ? "border-mint bg-mint/10 text-mint"
                  : "border-zinc-800 text-zinc-400 hover:border-zinc-600"
              }`}
            >
              {it.title}
            </button>
          ))}
        </div>
        <div className="pt-4 border-t border-zinc-800 space-y-2">
          <button
            type="button"
            onClick={loadOutputContract}
            className="w-full rounded-md border border-zinc-600 px-3 py-2 text-xs font-mono text-zinc-300"
          >
            Kontrakt wyjść agentów (JSON)
          </button>
          {contractOpen && (
            <pre className="text-[10px] text-zinc-500 max-h-40 overflow-auto whitespace-pre-wrap break-all">
              {contractJson || "…"}
            </pre>
          )}
        </div>
      </div>
      <div className="flex-1 min-w-0 space-y-4">
        {current && (
          <>
            <h2 className="text-lg font-mono text-zinc-200">{current.title}</h2>
            <p className="text-sm text-zinc-500">{current.description}</p>
            <textarea
              className="w-full min-h-[320px] rounded-lg border border-zinc-700 bg-black/50 p-4 font-mono text-sm leading-relaxed text-zinc-200"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={save}
                className="rounded-md bg-mint px-6 py-2 text-sm font-semibold text-black"
              >
                Save (nowa wersja)
              </button>
              <button
                type="button"
                onClick={reset}
                className="rounded-md border border-zinc-600 px-6 py-2 text-sm font-mono text-zinc-300"
              >
                Reset (usuń wersje)
              </button>
            </div>
            <div className="rounded-lg border border-zinc-800 overflow-hidden">
              <div className="px-3 py-2 bg-zinc-900 text-xs font-mono text-zinc-400">
                Wersje — {sel}
              </div>
              <table className="w-full text-left text-xs font-mono">
                <thead className="text-zinc-500 border-b border-zinc-800">
                  <tr>
                    <th className="p-2">v</th>
                    <th className="p-2">czas (UTC)</th>
                    <th className="p-2">aktywna</th>
                    <th className="p-2">podgląd</th>
                    <th className="p-2">akcje</th>
                  </tr>
                </thead>
                <tbody>
                  {versions.map((v) => (
                    <tr key={v.id} className="border-t border-zinc-800 text-zinc-300">
                      <td className="p-2 text-mint">{v.version}</td>
                      <td className="p-2 text-zinc-500 whitespace-nowrap">{v.created_at}</td>
                      <td className="p-2">{v.is_active ? "tak" : ""}</td>
                      <td className="p-2 max-w-[200px] truncate text-zinc-500">{v.preview}</td>
                      <td className="p-2 flex flex-wrap gap-1">
                        <button
                          type="button"
                          className="text-mint hover:underline"
                          onClick={() => loadVersionIntoEditor(v.id)}
                        >
                          wczytaj
                        </button>
                        {!v.is_active && (
                          <>
                            <button
                              type="button"
                              className="text-mint hover:underline"
                              onClick={() => activateVersion(v.id)}
                            >
                              aktywuj
                            </button>
                            <button
                              type="button"
                              className="text-red-400 hover:underline"
                              onClick={() => deleteVersionRow(v.id, v.is_active)}
                            >
                              usuń
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        {msg && <p className="text-sm font-mono text-mint">{msg}</p>}
        <div className="rounded-lg border border-zinc-800 p-4">
          <h3 className="text-sm font-mono text-zinc-400 mb-2">Placeholdery w promptach</h3>
          <ul className="text-xs font-mono text-zinc-500 space-y-1 max-h-48 overflow-y-auto">
            {ph.map((p) => (
              <li key={p.id}>
                <span className="text-mint">{`{${p.id}}`}</span> — {p.description}{" "}
                <span className="text-zinc-600">({p.context})</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
