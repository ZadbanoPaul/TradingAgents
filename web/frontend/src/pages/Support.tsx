export default function Support() {
  return (
    <div className="max-w-xl space-y-4 font-mono text-sm text-zinc-400">
      <h1 className="text-2xl text-mint">Support</h1>
      <p>
        Aplikacja „Zadbano investing masters” opiera się na frameworku badawczym TradingAgents.
        Dokumentacja upstream: repozytorium TauricResearch / TradingAgents oraz arXiv 2412.20138.
      </p>
      <p className="text-zinc-600">
        W tej instalacji raporty działają w tle (worker + SQLite). W razie błędów
        sprawdź logi workera i poprawność kluczy API.
      </p>
    </div>
  );
}
