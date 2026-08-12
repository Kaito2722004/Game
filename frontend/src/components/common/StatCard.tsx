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
  cooperate: "text-emerald-300",
  defect: "text-rose-300",
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
    <div className="card card-interactive p-5">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <p className="text-xs font-medium tracking-wide text-lab-600 uppercase">{label}</p>
          {hint ? <InfoTooltip text={hint} label={`About ${label}`} /> : null}
        </div>
        {icon ? <span className="text-lab-400">{icon}</span> : null}
      </div>

      {loading ? (
        <Skeleton className="mt-3 h-8 w-20" />
      ) : (
        <p className={`mt-2 text-2xl font-semibold tabular-nums ${TONE_TEXT[tone]}`}>{value}</p>
      )}

      {footer ? <div className="mt-2 text-xs text-lab-600">{footer}</div> : null}
    </div>
  );
}
