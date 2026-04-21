import { useState } from "react";
import { Auth, type User } from "../api";

export default function Login({
  onDone,
}: {
  onDone: (u: User) => void;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const u =
        mode === "login"
          ? await Auth.login(username, password)
          : await Auth.register(username, password, displayName || username);
      onDone(u);
    } catch (x) {
      setErr(x instanceof Error ? x.message : "Błąd");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-panel p-6">
      <div className="w-full max-w-md border border-zinc-800 rounded-xl p-8 bg-zinc-950/80">
        <h1 className="text-2xl font-mono text-mint mb-6">Zadbano investing masters</h1>
        <div className="flex gap-2 mb-6">
          <button
            type="button"
            className={`flex-1 rounded-md py-2 text-sm font-mono ${
              mode === "login" ? "bg-mint text-black" : "bg-zinc-900 text-zinc-400"
            }`}
            onClick={() => setMode("login")}
          >
            Logowanie
          </button>
          <button
            type="button"
            className={`flex-1 rounded-md py-2 text-sm font-mono ${
              mode === "register" ? "bg-mint text-black" : "bg-zinc-900 text-zinc-400"
            }`}
            onClick={() => setMode("register")}
          >
            Rejestracja
          </button>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-xs text-zinc-500 mb-1 font-mono">
              Użytkownik
            </label>
            <input
              className="w-full rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>
          {mode === "register" && (
            <div>
              <label className="block text-xs text-zinc-500 mb-1 font-mono">
                Wyświetlana nazwa
              </label>
              <input
                className="w-full rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>
          )}
          <div>
            <label className="block text-xs text-zinc-500 mb-1 font-mono">
              Hasło
            </label>
            <input
              type="password"
              className="w-full rounded-md border border-zinc-700 bg-black/40 px-3 py-2 font-mono text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
          </div>
          {err && <p className="text-sm text-red-400 font-mono">{err}</p>}
          <button
            type="submit"
            className="w-full rounded-md bg-mint py-2.5 text-sm font-semibold text-black"
          >
            {mode === "login" ? "Zaloguj" : "Utwórz konto"}
          </button>
        </form>
      </div>
    </div>
  );
}
