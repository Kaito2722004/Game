import { Loader2 } from "lucide-react";
import { cn } from "@/utils/cn";

export function Spinner({ className, label = "Loading" }: { className?: string; label?: string }) {
  return (
    <span role="status" aria-live="polite" className="inline-flex items-center gap-2">
      <Loader2 className={cn("h-5 w-5 animate-spin text-indigo-600", className)} aria-hidden />
      <span className="sr-only">{label}</span>
    </span>
  );
}

export function LoadingBlock({ label = "Loading data" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-sm text-slate-500">
      <Spinner label={label} />
      <p>{label}…</p>
    </div>
  );
}
