import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Jobs, type JobOut, type User } from "../api";

export default function Overview({ user }: { user: User }) {
  const [last, setLast] = useState<JobOut | null>(null);

  useEffect(() => {
    Jobs.list()
      .then((rows) => setLast(rows[0] ?? null))
      .catch(() => setLast(null));
  }, []);

  return (
    <div className="max-w-3xl space-y-8">
      <h1 className="text-3xl font-mono text-mint">
        Welcome back, {user.display_name || user.username}.
      </h1>
      <div className="border border-zinc-800 rounded-lg p-6 space-y-4 bg-zinc-950/50">
        <p className="text-sm text-zinc-400 font-mono">Szybkie akcje</p>
        <div className="flex flex-col gap-2">
          <Link
            to="/history"
            className="flex items-center gap-2 text-mint hover:text-mint-dim font-mono text-sm"
          >
            <span>▶</span> Run New Analysis
          </Link>
          <Link
            to="/api-keys"
            className="flex items-center gap-2 text-mint hover:text-mint-dim font-mono text-sm"
          >
            <span>▶</span> Manage API Keys
          </Link>
          <Link
            to="/prompts"
            className="flex items-center gap-2 text-mint hover:text-mint-dim font-mono text-sm"
          >
            <span>▶</span> Edit Prompts
          </Link>
        </div>
      </div>
      <div className="border border-zinc-800 rounded-lg p-6 bg-zinc-950/50">
        <h2 className="text-lg font-mono text-mint mb-2">Last analysis</h2>
        {last ? (
          <div className="text-sm text-zinc-400 font-mono space-y-1">
            <p>
              <span className="text-zinc-200">{last.ticker}</span> ·{" "}
              {last.trade_date} · status:{" "}
              <span className="text-mint">{last.status}</span>
            </p>
            {last.final_signal && (
              <p>
                Recommendation:{" "}
                <span
                  className={
                    /sell|underweight/i.test(last.final_signal)
                      ? "text-red-400"
                      : "text-mint"
                  }
                >
                  {last.final_signal}
                </span>
              </p>
            )}
            {last.duration_ms != null && last.status === "completed" && (
              <p>Duration: {(last.duration_ms / 1000 / 60).toFixed(1)} min</p>
            )}
            <Link to="/history" className="inline-block mt-2 text-mint text-sm">
              View full history →
            </Link>
          </div>
        ) : (
          <p className="text-zinc-500 font-mono text-sm">Brak jeszcze raportów.</p>
        )}
      </div>
    </div>
  );
}
