import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

type Tone = "neutral" | "cooperate" | "defect" | "info" | "warning" | "success" | "accent";

/** Translucent fills over the dark surface, each with a matching hairline ring. */
const TONES: Record<Tone, string> = {
  neutral: "bg-lab-200/80 text-lab-700 ring-lab-300",
  cooperate: "bg-emerald-400/12 text-emerald-300 ring-emerald-400/30",
  defect: "bg-rose-500/12 text-rose-300 ring-rose-500/30",
  info: "bg-sky-500/12 text-sky-300 ring-sky-500/30",
  warning: "bg-amber-400/12 text-amber-200 ring-amber-400/30",
  success: "bg-emerald-400/12 text-emerald-300 ring-emerald-400/30",
  accent: "bg-violet-500/15 text-violet-300 ring-violet-500/35",
};

interface BadgeProps {
  children: ReactNode;
  tone?: Tone;
  icon?: ReactNode;
  className?: string;
  title?: string;
}

export function Badge({ children, tone = "neutral", icon, className, title }: BadgeProps) {
  return (
    <span
      title={title}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        TONES[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}
