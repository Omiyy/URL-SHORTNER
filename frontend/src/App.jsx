import { NavLink, Route, Routes } from "react-router-dom";

import HomePage from "./pages/HomePage";
import StatsPage from "./pages/StatsPage";

const navClass = ({ isActive }) =>
  `rounded-full px-4 py-2 text-sm font-semibold transition ${isActive ? "bg-ink text-white" : "bg-white/70 text-ink hover:bg-white"}`;

export default function App() {
  return (
    <div className="mx-auto min-h-screen max-w-4xl px-4 py-8 md:py-12">
      <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="font-display text-xl font-bold tracking-tight">FastURL</p>
          <p className="text-sm text-ink/70">Bitly-like URL shortener for high-throughput workloads</p>
        </div>
        <nav className="flex items-center gap-2">
          <NavLink to="/" className={navClass} end>
            Home
          </NavLink>
          <NavLink to="/stats" className={navClass}>
            Stats
          </NavLink>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/stats" element={<StatsPage />} />
        </Routes>
      </main>
    </div>
  );
}
