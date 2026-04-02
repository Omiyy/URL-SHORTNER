export default function UrlForm({
  value,
  onChange,
  onSubmit,
  loading,
  placeholder,
  buttonText
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-ink/20 bg-white/80 px-4 py-3 text-sm outline-none transition focus:border-coral focus:ring-2 focus:ring-coral/30"
        placeholder={placeholder}
        required
      />
      <button
        disabled={loading}
        className="w-full rounded-xl bg-ink px-4 py-3 font-semibold text-white transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {loading ? "Please wait..." : buttonText}
      </button>
    </form>
  );
}
