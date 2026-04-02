import { useState } from "react";
import toast from "react-hot-toast";

import { api } from "../api/client";
import UrlForm from "../components/UrlForm";

export default function HomePage() {
  const [url, setUrl] = useState("");
  const [shortUrl, setShortUrl] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);

    try {
      const response = await api.post("/api/shorten", { url });
      setShortUrl(response.data.short_url);
      toast.success("Short URL generated");
    } catch (error) {
      const message = error.response?.data?.detail || "Failed to shorten URL";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shortUrl);
      toast.success("Copied to clipboard");
    } catch (_error) {
      toast.error("Clipboard copy failed");
    }
  };

  return (
    <section className="reveal rounded-3xl bg-white/70 p-6 shadow-panel backdrop-blur-sm md:p-8">
      <h1 className="font-display text-3xl font-bold md:text-4xl">Shorten in Seconds</h1>
      <p className="mt-2 text-sm text-ink/75">
        Build compact links with Redis-accelerated redirects and low-write analytics.
      </p>

      <div className="mt-6">
        <UrlForm
          value={url}
          onChange={setUrl}
          onSubmit={handleSubmit}
          loading={loading}
          placeholder="https://example.com/very/long/path"
          buttonText="Shorten URL"
        />
      </div>

      {shortUrl && (
        <div className="mt-6 rounded-2xl border border-mint/30 bg-mint/10 p-4">
          <p className="text-xs uppercase tracking-wider text-ink/70">Generated URL</p>
          <a href={shortUrl} className="mt-1 block break-all font-semibold text-ink underline" target="_blank" rel="noreferrer">
            {shortUrl}
          </a>
          <button onClick={handleCopy} className="mt-3 rounded-lg bg-coral px-3 py-2 text-sm font-semibold text-white">
            Copy Link
          </button>
        </div>
      )}
    </section>
  );
}
