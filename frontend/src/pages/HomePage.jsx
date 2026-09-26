import { Link } from "react-router-dom";
import { ArrowRight, Link2, BarChart3, Zap, Shield } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="animate-fade-in">
      {/* ── Hero ── */}
      <section className="py-12 sm:py-20 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3.5 py-1 text-xs font-medium text-brand-700 mb-6">
          <Zap className="h-3.5 w-3.5" />
          Redis-accelerated redirects
        </div>

        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
          Short links,{" "}
          <span className="text-brand-600">fast redirects</span>
        </h1>

        <p className="mx-auto mt-4 max-w-lg text-base text-slate-500 sm:text-lg">
          Create compact, memorable URLs in seconds.
          Track clicks and manage everything from a clean dashboard.
        </p>

        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          {isAuthenticated ? (
            <Link to="/dashboard" className="btn-primary text-base px-6 py-3">
              Go to Dashboard
              <ArrowRight className="h-4 w-4" />
            </Link>
          ) : (
            <>
              <Link to="/register" className="btn-primary text-base px-6 py-3">
                Get started — it's free
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/login" className="btn-secondary text-base px-6 py-3">
                Sign in
              </Link>
            </>
          )}
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="py-12">
        <h2 className="text-center text-sm font-semibold uppercase tracking-wider text-slate-400 mb-10">
          How it works
        </h2>
        <div className="grid gap-6 sm:grid-cols-3">
          {[
            {
              step: "1",
              title: "Paste your URL",
              desc: "Drop in any long link — the original URL stays unchanged.",
            },
            {
              step: "2",
              title: "Get a short link",
              desc: "We generate a compact code, or you can set a custom alias.",
            },
            {
              step: "3",
              title: "Share & track",
              desc: "Use your short link anywhere and watch the click count grow.",
            },
          ].map((item) => (
            <div key={item.step} className="card p-6 text-center group hover:shadow-card-hover transition-shadow duration-200">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 text-brand-700 font-bold text-sm mb-4 group-hover:bg-brand-600 group-hover:text-white transition-colors duration-200">
                {item.step}
              </div>
              <h3 className="font-semibold text-slate-800">{item.title}</h3>
              <p className="mt-1.5 text-sm text-slate-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-12">
        <h2 className="text-center text-sm font-semibold uppercase tracking-wider text-slate-400 mb-10">
          Features
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              icon: Link2,
              title: "Custom Aliases",
              desc: "Choose memorable short codes or let FastURL generate one automatically.",
            },
            {
              icon: BarChart3,
              title: "Click Tracking",
              desc: "Monitor total click counts per link in real time.",
            },
            {
              icon: Zap,
              title: "Redis-Powered",
              desc: "Sub-millisecond redirects through in-memory caching.",
            },
            {
              icon: Shield,
              title: "Secure Auth",
              desc: "JWT access tokens with HttpOnly refresh cookies for safe sessions.",
            },
            {
              icon: Link2,
              title: "Soft Deletes",
              desc: "Deactivate links without losing historical data.",
            },
            {
              icon: BarChart3,
              title: "Dashboard",
              desc: "Manage all your links, search, copy, and delete from one place.",
            },
          ].map((feature) => (
            <div key={feature.title} className="card p-5 group hover:shadow-card-hover transition-shadow duration-200">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 mb-3 group-hover:bg-brand-600 group-hover:text-white transition-colors duration-200">
                <feature.icon className="h-4.5 w-4.5" />
              </div>
              <h3 className="font-semibold text-slate-800 text-sm">{feature.title}</h3>
              <p className="mt-1 text-sm text-slate-500">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      {!isAuthenticated && (
        <section className="py-12 text-center">
          <div className="card mx-auto max-w-xl p-8 sm:p-10 bg-gradient-to-br from-brand-50 to-white border-brand-100">
            <h2 className="text-2xl font-bold text-slate-900">
              Ready to shorten your links?
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Create a free account and start building short URLs today.
            </p>
            <Link
              to="/register"
              className="btn-primary mt-6 inline-flex text-base px-6 py-3"
            >
              Create free account
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
