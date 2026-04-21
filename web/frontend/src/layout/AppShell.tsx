import { NavLink, Outlet } from "react-router-dom";
import type { User } from "../api";

const nav = [
  { to: "/", label: "Overview" },
  { to: "/history", label: "History" },
  { to: "/api-keys", label: "API Keys" },
  { to: "/prompts", label: "Prompts" },
  { to: "/process", label: "Process (BPMN)" },
  { to: "/data-catalog", label: "Data catalog" },
  { to: "/market-lab", label: "Market lab" },
  { to: "/support", label: "Support" },
];

export default function AppShell({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  return (
    <div className="min-h-screen flex flex-col bg-panel text-zinc-200">
      <header className="h-14 border-b border-zinc-800 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3">
          <svg
            width="28"
            height="28"
            viewBox="0 0 32 32"
            fill="none"
            className="text-white"
          >
            <path
              d="M4 20 Q10 8 16 16 T28 12"
              stroke="currentColor"
              strokeWidth="2"
              fill="none"
            />
          </svg>
          <span className="font-mono text-sm text-zinc-500">Zadbano investing masters</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-zinc-400 hidden sm:inline">
            {user.display_name}
          </span>
          <button
            type="button"
            className="rounded-full bg-mint px-4 py-1.5 text-sm font-medium text-black"
          >
            Account
          </button>
        </div>
      </header>
      <div className="flex flex-1 min-h-0">
        <aside className="w-52 border-r border-zinc-800 flex flex-col py-4 shrink-0">
          <nav className="flex flex-col gap-1 px-2">
            {nav.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                className={({ isActive }) =>
                  `rounded-md px-3 py-2 text-sm font-mono transition-colors ${
                    isActive
                      ? "bg-mint/15 text-mint"
                      : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="mt-auto border-t border-zinc-800 pt-4 px-4">
            <button
              type="button"
              onClick={onLogout}
              className="text-sm font-mono text-red-400 hover:text-red-300"
            >
              Sign Out
            </button>
          </div>
        </aside>
        <main className="flex-1 overflow-auto p-6 lg:p-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
