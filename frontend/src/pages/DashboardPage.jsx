import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ExternalLink,
  Plus,
  Search,
  Trash2,
  BarChart3,
  X,
  MousePointerClick,
} from "lucide-react";
import toast from "react-hot-toast";

import { useAuth } from "../context/AuthContext";
import {
  createShortUrl,
  getUrls,
  getUrlStats,
  deleteUrl,
  extractErrorMessage,
} from "../api";
import CopyButton from "../components/CopyButton";
import EmptyState from "../components/EmptyState";
import ErrorAlert from "../components/ErrorAlert";
import Spinner from "../components/Spinner";

export default function DashboardPage() {
  const { user } = useAuth();
  const [urls, setUrls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Create URL form
  const [showCreate, setShowCreate] = useState(false);
  const [originalUrl, setOriginalUrl] = useState("");
  const [customAlias, setCustomAlias] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [justCreated, setJustCreated] = useState(null);

  // Search
  const [searchQuery, setSearchQuery] = useState("");

  // Stats modal
  const [statsCode, setStatsCode] = useState(null);
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  // Delete confirmation
  const [deletingCode, setDeletingCode] = useState(null);

  // Fetch URLs on mount
  const fetchUrls = useCallback(async () => {
    try {
      setError("");
      const data = await getUrls();
      setUrls(data);
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to load your URLs"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUrls();
  }, [fetchUrls]);

  // Client-side search filter
  const filteredUrls = useMemo(() => {
    if (!searchQuery.trim()) return urls;
    const q = searchQuery.toLowerCase();
    return urls.filter(
      (u) =>
        u.short_code.toLowerCase().includes(q) ||
        u.original_url.toLowerCase().includes(q) ||
        u.short_url.toLowerCase().includes(q)
    );
  }, [urls, searchQuery]);

  // Create URL handler
  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateError("");
    setCreating(true);
    setJustCreated(null);

    try {
      const newUrl = await createShortUrl({
        original_url: originalUrl.trim(),
        custom_alias: customAlias.trim() || undefined,
      });
      setUrls((prev) => [newUrl, ...prev]);
      setJustCreated(newUrl);
      setOriginalUrl("");
      setCustomAlias("");
      toast.success("Short URL created!");
    } catch (err) {
      setCreateError(extractErrorMessage(err, "Failed to create short URL"));
    } finally {
      setCreating(false);
    }
  };

  // Fetch stats
  const handleViewStats = async (shortCode) => {
    setStatsCode(shortCode);
    setStats(null);
    setStatsLoading(true);

    try {
      const data = await getUrlStats(shortCode);
      setStats(data);
    } catch (err) {
      toast.error(extractErrorMessage(err, "Failed to load stats"));
      setStatsCode(null);
    } finally {
      setStatsLoading(false);
    }
  };

  // Delete URL
  const handleDelete = async (shortCode) => {
    try {
      await deleteUrl(shortCode);
      setUrls((prev) => prev.filter((u) => u.short_code !== shortCode));
      setDeletingCode(null);
      if (statsCode === shortCode) {
        setStatsCode(null);
        setStats(null);
      }
      toast.success("Link deleted");
    } catch (err) {
      toast.error(extractErrorMessage(err, "Failed to delete link"));
    }
  };

  // Format date
  const formatDate = (iso) => {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="animate-fade-in">
      {/* ── Header ── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500">
            {user?.user_name ? `Welcome, ${user.user_name}` : "Manage your short links"}
          </p>
        </div>
        <button
          onClick={() => {
            setShowCreate(!showCreate);
            setJustCreated(null);
            setCreateError("");
          }}
          className="btn-primary"
        >
          {showCreate ? (
            <>
              <X className="h-4 w-4" />
              Cancel
            </>
          ) : (
            <>
              <Plus className="h-4 w-4" />
              New short link
            </>
          )}
        </button>
      </div>

      {/* ── Create form ── */}
      {showCreate && (
        <div className="card p-5 mb-6 animate-slide-down">
          <h2 className="text-base font-semibold text-slate-800 mb-4">
            Shorten a URL
          </h2>
          <form onSubmit={handleCreate} className="space-y-3">
            <ErrorAlert message={createError} />

            <div>
              <label htmlFor="create-url" className="label">
                Destination URL
              </label>
              <input
                id="create-url"
                type="url"
                value={originalUrl}
                onChange={(e) => setOriginalUrl(e.target.value)}
                className="input-field"
                placeholder="https://example.com/a/very/long/path"
                required
                disabled={creating}
              />
            </div>

            <div>
              <label htmlFor="create-alias" className="label">
                Custom alias{" "}
                <span className="font-normal text-slate-400">(optional)</span>
              </label>
              <input
                id="create-alias"
                type="text"
                value={customAlias}
                onChange={(e) => setCustomAlias(e.target.value)}
                className="input-field"
                placeholder="my-link"
                minLength={3}
                maxLength={32}
                disabled={creating}
              />
            </div>

            <button
              type="submit"
              disabled={creating}
              className="btn-primary"
            >
              {creating ? (
                <Spinner size="sm" className="text-white" />
              ) : null}
              {creating ? "Creating…" : "Create short link"}
            </button>
          </form>

          {/* Just-created result */}
          {justCreated && (
            <div className="mt-4 rounded-lg border border-brand-200 bg-brand-50 p-4 animate-scale-in">
              <p className="text-xs font-medium text-brand-700 uppercase tracking-wider mb-2">
                Your new short link
              </p>
              <div className="flex items-center gap-2">
                <a
                  href={justCreated.short_url}
                  target="_blank"
                  rel="noreferrer"
                  className="short-url-display hover:underline"
                >
                  {justCreated.short_url}
                </a>
                <CopyButton text={justCreated.short_url} />
                <a
                  href={justCreated.short_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-ghost p-1.5"
                  title="Open link"
                >
                  <ExternalLink className="h-4 w-4 text-slate-400" />
                </a>
              </div>
              <p className="mt-1.5 text-xs text-slate-500 truncate">
                → {justCreated.original_url}
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── Search ── */}
      {urls.length > 0 && (
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-9"
            placeholder="Search by URL or short code…"
          />
        </div>
      )}

      {/* ── URL list ── */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : error ? (
        <ErrorAlert message={error} />
      ) : urls.length === 0 ? (
        <EmptyState
          title="No links yet"
          description="Create your first short link to get started."
          action={
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              <Plus className="h-4 w-4" />
              Create your first link
            </button>
          }
        />
      ) : filteredUrls.length === 0 ? (
        <EmptyState
          title="No results"
          description={`No links match "${searchQuery}"`}
        />
      ) : (
        <div className="space-y-3">
          {filteredUrls.map((url, idx) => (
            <div
              key={url.short_code}
              className="card-hover p-4 sm:p-5 animate-slide-up"
              style={{ animationDelay: `${Math.min(idx * 50, 300)}ms` }}
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                {/* Left: URL info */}
                <div className="min-w-0 flex-1">
                  {/* Short URL — signature moment */}
                  <div className="flex items-center gap-2">
                    <a
                      href={url.short_url}
                      target="_blank"
                      rel="noreferrer"
                      className="short-url-display hover:underline truncate"
                    >
                      {url.short_url}
                    </a>
                    <CopyButton text={url.short_url} />
                    <a
                      href={url.short_url}
                      target="_blank"
                      rel="noreferrer"
                      className="btn-ghost p-1.5 flex-shrink-0"
                      title="Open link"
                    >
                      <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
                    </a>
                  </div>

                  {/* Original URL */}
                  <p className="mt-1 text-sm text-slate-500 truncate">
                    {url.original_url}
                  </p>

                  {/* Meta row */}
                  <div className="mt-2 flex items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <MousePointerClick className="h-3 w-3" />
                      {url.no_of_clicks} {url.no_of_clicks === 1 ? "click" : "clicks"}
                    </span>
                    <span>{formatDate(url.created_at)}</span>
                  </div>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => handleViewStats(url.short_code)}
                    className="btn-ghost text-xs"
                    title="View stats"
                  >
                    <BarChart3 className="h-4 w-4" />
                    <span className="hidden sm:inline">Stats</span>
                  </button>

                  {deletingCode === url.short_code ? (
                    <div className="flex items-center gap-1 animate-scale-in">
                      <button
                        onClick={() => handleDelete(url.short_code)}
                        className="btn-danger text-xs"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => setDeletingCode(null)}
                        className="btn-ghost text-xs"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setDeletingCode(url.short_code)}
                      className="btn-ghost text-xs text-slate-400 hover:text-red-600"
                      title="Delete link"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Stats modal overlay ── */}
      {statsCode && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 backdrop-blur-sm p-4 animate-fade-in"
          onClick={() => {
            setStatsCode(null);
            setStats(null);
          }}
        >
          <div
            className="w-full max-w-md rounded-xl bg-white shadow-modal p-6 animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900">
                Link Stats
              </h2>
              <button
                onClick={() => {
                  setStatsCode(null);
                  setStats(null);
                }}
                className="btn-ghost p-1.5"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {statsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="lg" />
              </div>
            ) : stats ? (
              <div className="space-y-4">
                {/* Short code */}
                <div>
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Short Code
                  </p>
                  <p className="short-url-display text-lg mt-0.5">
                    {stats.short_code}
                  </p>
                </div>

                {/* Original URL */}
                <div>
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Destination
                  </p>
                  <p className="mt-0.5 text-sm text-slate-700 break-all">
                    {stats.original_url}
                  </p>
                </div>

                {/* Clicks */}
                <div className="rounded-lg bg-brand-50 border border-brand-100 p-4 text-center">
                  <p className="text-xs font-medium text-brand-600 uppercase tracking-wider">
                    Total Clicks
                  </p>
                  <p className="text-4xl font-bold text-brand-700 mt-1">
                    {stats.no_of_clicks.toLocaleString()}
                  </p>
                </div>

                {/* Created */}
                <div>
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Created
                  </p>
                  <p className="mt-0.5 text-sm text-slate-700">
                    {new Date(stats.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
