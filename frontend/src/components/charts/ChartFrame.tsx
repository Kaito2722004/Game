import type { ReactNode } from "react";
import { InfoTooltip } from "@/components/common/InfoTooltip";

interface ChartFrameProps {
  title: string;
  description?: string;
  hint?: string;
  height?: number;
  actions?: ReactNode;
  children: ReactNode;
}

/**
 * Shared shell for every chart: a titled, described container with a fixed
 * height so the responsive Recharts container has something to fill.
 */
export function ChartFrame({
  title,
  description,
  hint,
  height = 300,
  actions,
  children,
}: ChartFrameProps) {
  return (
    <figure className="card p-5">
      <figcaption className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-1.5">
            <h3 className="text-sm font-semibold text-lab-950">{title}</h3>
            {hint ? <InfoTooltip text={hint} label={`About ${title}`} /> : null}
          </div>
          {description ? <p className="mt-0.5 text-xs text-slate-500">{description}</p> : null}
        </div>
        {actions}
      </figcaption>

      <div style={{ height }}>{children}</div>
    </figure>
  );
}
