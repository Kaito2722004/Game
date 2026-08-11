import type { ReactNode } from "react";
import { InfoTooltip } from "./InfoTooltip";
import { Skeleton } from "./Skeleton";

interface StatCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  tone?: "default" | "cooperate" | "defect";
  loading?: boolean;
  footer?: ReactNode;
}

const TONE_TEXT = {
  default: "text-lab-950",
  cooperate: "text-green-800",
  defect: "text-red-800",
} as const;

export function StatCard({
  label,
  value,
  hint,
  icon,
  tone = "default",
  loading = false,
  footer,
}: StatCardProps) {
  return (
    <div className="card p-5 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">{label}</p>
          {hint ? <InfoTooltip text={hint} label={`About ${label}`} /> : null}
        </div>
        {icon ? <span className="text-lab-400">{icon}</span> : null}
      </div>

      {loading ? (
        <Skeleton className="mt-3 h-8 w-20" />
      ) : (
        <p className={`mt-2 text-2xl font-semibold tabular-nums ${TONE_TEXT[tone]}`}>{value}</p>
      )}

      {footer ? <div className="mt-2 text-xs text-slate-500">{footer}</div> : null}
    </div>
  );
}
