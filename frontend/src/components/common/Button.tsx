import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/utils/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "cooperate" | "defect";
type Size = "sm" | "md" | "lg";

/**
 * Primary carries the violet gradient and a soft glow; everything else stays
 * quiet so a screen never has two things shouting at once. Cooperate and
 * defect keep their own colours because those two carry meaning in the game.
 */
const VARIANTS: Record<Variant, string> = {
  primary: cn(
    "bg-gradient-to-br from-violet-600 to-purple-500 text-white",
    "shadow-[0_4px_16px_-4px_rgb(139_92_246/0.5)]",
    "hover:from-violet-500 hover:to-purple-400 hover:shadow-[0_6px_22px_-4px_rgb(139_92_246/0.65)]",
    "disabled:from-violet-500/30 disabled:to-purple-500/30 disabled:text-white/50 disabled:shadow-none",
  ),
  secondary: cn(
    "border border-lab-300 bg-lab-200/60 text-lab-800 backdrop-blur-sm",
    "hover:border-violet-500/50 hover:bg-lab-200 hover:text-white",
    "disabled:text-lab-500 disabled:hover:border-lab-300",
  ),
  ghost: "text-lab-700 hover:bg-lab-200/70 hover:text-white disabled:text-lab-500",
  danger: cn(
    "bg-gradient-to-br from-rose-600 to-rose-500 text-white",
    "shadow-[0_4px_16px_-4px_rgb(244_63_94/0.45)]",
    "hover:from-rose-500 hover:to-rose-400",
    "disabled:from-rose-500/30 disabled:to-rose-500/30 disabled:text-white/50 disabled:shadow-none",
  ),
  cooperate: cn(
    "bg-gradient-to-br from-emerald-600 to-emerald-500 text-white",
    "shadow-[0_4px_16px_-4px_rgb(52_211_153/0.45)]",
    "hover:from-emerald-500 hover:to-emerald-400",
    "disabled:from-emerald-500/30 disabled:to-emerald-500/30 disabled:text-white/50 disabled:shadow-none",
  ),
  defect: cn(
    "bg-gradient-to-br from-rose-600 to-pink-500 text-white",
    "shadow-[0_4px_16px_-4px_rgb(251_113_133/0.45)]",
    "hover:from-rose-500 hover:to-pink-400",
    "disabled:from-rose-500/30 disabled:to-pink-500/30 disabled:text-white/50 disabled:shadow-none",
  ),
};

const SIZES: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs gap-1.5 rounded-lg",
  md: "px-4 py-2 text-sm gap-2 rounded-xl",
  lg: "px-5 py-2.5 text-base gap-2 rounded-xl",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
  fullWidth?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  fullWidth,
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      type="button"
      {...rest}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(
        "inline-flex items-center justify-center font-medium",
        "transition-all duration-200 ease-out",
        // A very small lift on hover. Anything larger reads as a toy.
        "hover:-translate-y-px active:translate-y-0 active:scale-[0.98]",
        "disabled:cursor-not-allowed disabled:translate-y-0 disabled:active:scale-100",
        VARIANTS[variant],
        SIZES[size],
        fullWidth && "w-full",
        className,
      )}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : icon}
      {children}
    </button>
  );
}
