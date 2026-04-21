import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Auth, type User } from "./api";
import AppShell from "./layout/AppShell";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import History from "./pages/History";
import ApiKeys from "./pages/ApiKeys";
import Prompts from "./pages/Prompts";
import Live from "./pages/Live";
import ReportCharts from "./pages/ReportCharts";
import Support from "./pages/Support";
import ProcessBpmnPage from "./pages/ProcessBpmnPage";
import DataCatalogPage from "./pages/DataCatalogPage";
import MarketLabPage from "./pages/MarketLabPage";

export default function App() {
  const [user, setUser] = useState<User | null | undefined>(undefined);

  useEffect(() => {
    Auth.me()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function logout() {
    await Auth.logout();
    setUser(null);
  }

  if (user === undefined) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-panel text-zinc-500 font-mono text-sm">
        Ładowanie…
      </div>
    );
  }

  if (!user) {
    return <Login onDone={setUser} />;
  }

  return (
    <Routes>
      <Route element={<AppShell user={user} onLogout={logout} />}>
        <Route index element={<Overview user={user} />} />
        <Route path="history" element={<History />} />
        <Route path="api-keys" element={<ApiKeys />} />
        <Route path="prompts" element={<Prompts />} />
        <Route path="support" element={<Support />} />
        <Route path="live/:id" element={<Live />} />
        <Route path="live/:id/charts" element={<ReportCharts />} />
        <Route path="process" element={<ProcessBpmnPage />} />
        <Route path="data-catalog" element={<DataCatalogPage />} />
        <Route path="market-lab" element={<MarketLabPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
