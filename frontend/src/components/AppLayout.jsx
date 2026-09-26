import { Link, useLocation } from "react-router-dom";
import { LogOut, Link2, LayoutDashboard } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function AppLayout({ children }) {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <div className="flex min-h-screen flex-col">
      {/* ── Header ── */}
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          {/* Logo / wordmark */}
          <Link to="/" className="flex items-center gap-2 group">
            <span className="text-xl font-bold tracking-tight text-slate-900 group-hover:text-brand-600 transition-colors">
              Fast<span className="text-brand-600">URL</span>
            </span>
          </Link>

          {/* Nav */}
          <nav className="flex items-center gap-1">
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className={`btn-ghost text-sm ${
                    isActive("/dashboard") ? "bg-brand-50 text-brand-700" : ""
                  }`}
                >
                  <LayoutDashboard className="h-4 w-4" />
                  <span className="hidden sm:inline">Dashboard</span>
                </Link>
                <div className="mx-2 h-5 w-px bg-slate-200" />
                <span className="hidden text-sm font-medium text-slate-500 sm:block mr-2">
                  {user?.user_name}
                </span>
                <button
                  onClick={logout}
                  className="btn-ghost text-sm text-slate-500 hover:text-red-600"
                  title="Sign out"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden sm:inline">Sign out</span>
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className={`btn-ghost text-sm ${
                    isActive("/login") ? "bg-brand-50 text-brand-700" : ""
                  }`}
                >
                  Sign in
                </Link>
                <Link to="/register" className="btn-primary text-sm">
                  Get started
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* ── Main content ── */}
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
          {children}
        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-100 py-6">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="text-center text-xs text-slate-400">
            © {new Date().getFullYear()} FastURL · Built with React & FastAPI
          </p>
        </div>
      </footer>
    </div>
  );
}
