import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Settings, type ApiKeyStatus } from "../api";

export default function ApiKeys() {
  const [st, setSt] = useState<ApiKeyStatus | null>(null);
  const [openai, setOpenai] = useState("");
  const [av, setAv] = useState("");
  const [showO, setShowO] = useState(false);
  const [showA, setShowA] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    Settings.keys().then(setSt).catch(() => setSt(null));
  }, []);

  async function save() {
    setMsg(null);
    try {
      const body: Record<string, string | undefined> = {};
      if (openai !== "") body.openai_api_key = openai;
      if (av !== "") body.alpha_vantage_api_key = av;
      const r = await Settings.saveKeys(body);
      setSt(r);
      setOpenai("");
      setAv("");
      setMsg("Zapisano.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Błąd");
    }
  }

  return (
    <div className="max-w-2xl space-y-8">
      <h1 className="text-3xl font-mono text-mint">API Keys</h1>
      <p className="text-sm text-zinc-500 font-mono flex items-center gap-2">
        <span aria-hidden>🔒</span> Klucze są szyfrowane w bazie (nie plaintext).
      </p>
      {st && (
        <div className="space-y-2 text-sm font-mono">
          <p className={st.openai_configured ? "text-mint" : "text-zinc-500"}>
            {st.openai_configured ? "✓" : "○"} OpenAI —{" "}
            {st.openai_configured ? "skonfigurowany" : "brak"}
          </p>
          <p className={st.alpha_vantage_configured ? "text-mint" : "text-zinc-500"}>
            {st.alpha_vantage_configured ? "✓" : "○"} Alpha Vantage —{" "}
            {st.alpha_vantage_configured ? "skonfigurowany" : "brak"}
          </p>
        </div>
      )}

      <div className="border border-zinc-800 rounded-lg p-6 space-y-4 bg-zinc-950/50">
        <label className="block text-xs text-zinc-500 font-mono">LLM provider</label>
        <div className="flex gap-2">
          <input
            type={showO ? "text" : "password"}
            className="flex-1 rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm"
            placeholder="OpenAI API key"
            value={openai}
            onChange={(e) => setOpenai(e.target.value)}
          />
          <button
            type="button"
            className="px-3 rounded-md border border-zinc-700 text-xs font-mono"
            onClick={() => setShowO(!showO)}
          >
            eye
          </button>
          <button
            type="button"
            className="px-3 rounded-md border border-zinc-700 text-xs font-mono"
            onClick={() => setOpenai("")}
          >
            Clear
          </button>
        </div>
        <p className="text-xs text-zinc-600">
          BYOK: jeden klucz na konto; zapis nadpisuje poprzedni. Wymagany do kolejki
          analiz.
        </p>
      </div>

      <div className="border border-zinc-800 rounded-lg p-6 space-y-4 bg-zinc-950/50">
        <label className="block text-xs text-zinc-500 font-mono">
          Alpha Vantage API Key
        </label>
        <div className="flex gap-2">
          <input
            type={showA ? "text" : "password"}
            className="flex-1 rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm"
            placeholder="Opcjonalnie — jeśli używasz Alpha Vantage"
            value={av}
            onChange={(e) => setAv(e.target.value)}
          />
          <button
            type="button"
            className="px-3 rounded-md border border-zinc-700 text-xs font-mono"
            onClick={() => setShowA(!showA)}
          >
            eye
          </button>
          <button
            type="button"
            className="px-3 rounded-md border border-zinc-700 text-xs font-mono"
            onClick={() => setAv("")}
          >
            Clear
          </button>
        </div>
      </div>

      {msg && <p className="text-sm font-mono text-mint">{msg}</p>}

      <button
        type="button"
        onClick={save}
        className="w-full rounded-md bg-mint py-3 text-sm font-semibold text-black"
      >
        Save keys
      </button>

      <Link
        to="/history"
        className="block w-full text-center rounded-md border border-mint/40 py-3 text-sm font-mono text-mint hover:bg-mint/10"
      >
        Run New Analysis
      </Link>
    </div>
  );
}
