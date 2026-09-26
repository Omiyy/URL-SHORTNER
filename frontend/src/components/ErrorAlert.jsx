import { AlertCircle, Info } from "lucide-react";

export default function ErrorAlert({ message, variant = "error" }) {
  if (!message) return null;

  const isInfo = variant === "info";

  return (
    <div
      role="alert"
      className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm animate-slide-down ${
        isInfo
          ? "border-brand-200 bg-brand-50 text-brand-800"
          : "border-red-200 bg-red-50 text-red-700"
      }`}
    >
      {isInfo ? (
        <Info className="mt-0.5 h-4 w-4 flex-shrink-0" />
      ) : (
        <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
      )}
      <p>{message}</p>
    </div>
  );
}
