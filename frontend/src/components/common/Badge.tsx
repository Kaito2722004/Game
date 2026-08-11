import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

type Tone = "neutral" | "cooperate" | "defect" | "info" | "warning" | "success" | "accent";

const TONES: Record<Tone, string> = {
  neutral: "bg-lab-100 text-lab-700 ring-lab-200",
  cooperate: "bg-cooperate-soft text-green-900 ring-green-200",
  defect: "bg-defect-soft text-red-900 ring-red-200",
  info: "bg-blue-50 text-blue-800 ring-blue-200",
  warning: "bg-amber-50 text-amber-900 ring-amber-200",
  success: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  accent: "bg-indigo-50 text-indigo-800 ring-indigo-200",
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
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        TONES[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}
