import { Loader2 } from "lucide-react";

const sizes = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-8 w-8",
};

export default function Spinner({ size = "md", className = "" }) {
  return (
    <Loader2
      className={`animate-spin text-brand-500 ${sizes[size] || sizes.md} ${className}`}
    />
  );
}
