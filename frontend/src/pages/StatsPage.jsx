import { useState } from "react";
import toast from "react-hot-toast";

import { api } from "../api/client";
import UrlForm from "../components/UrlForm";

function extractCode(input) {
  if (!input) {
    return "";
  }

  try {
    const parsed = new URL(input);
    return parsed.pathname.replace(/^\//, "");
  } catch (_error) {
    return input.replace(/^\//, "");
  }
}

export default function StatsPage() {
  const [codeInput, setCodeInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const code = extractCode(codeInput);

    if (!code) {
      toast.error("Please enter a short code or short URL");
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(`/api/stats/${code}`);
      setStats(response.data);
      toast.success("Stats loaded");
    } catch (error) {
      const message = error.response?.data?.detail || "Could not fetch stats";
      toast.error(message);
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="reveal rounded-3xl bg-white/70 p-6 shadow-panel backdrop-blur-sm md:p-8">
      <h1 className="font-display text-3xl font-bold md:text-4xl">URL Analytics</h1>
      <p className="mt-2 text-sm text-ink/75">Check click counts and lifecycle data for any short link.</p>

      <div className="mt-6">
        <UrlForm
          value={codeInput}
          onChange={setCodeInput}
          onSubmit={handleSubmit}
          loading={loading}
          placeholder="Paste code or URL (e.g. http://localhost/abc123)"
          buttonText="Fetch Stats"
        />
      </div>

      {stats && (
        <div className="mt-6 grid gap-3 rounded-2xl border border-ink/10 bg-white/90 p-4 md:grid-cols-2">
          <div>
            <p className="text-xs uppercase text-ink/60">Original URL</p>
            <p className="break-all font-semibold text-ink">{stats.original_url}</p>
          </div>
          <div>
            <p className="text-xs uppercase text-ink/60">Total Clicks</p>
            <p className="font-display text-3xl font-bold text-coral">{stats.clicks}</p>
          </div>
          <div>
            <p className="text-xs uppercase text-ink/60">Created At</p>
            <p>{new Date(stats.created_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs uppercase text-ink/60">Last Accessed</p>
            <p>{stats.last_accessed ? new Date(stats.last_accessed).toLocaleString() : "Never"}</p>
          </div>
        </div>
      )}
    </section>
  );
}
