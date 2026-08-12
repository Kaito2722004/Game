import { Handshake, Swords } from "lucide-react";
import type { Action } from "@/types";
import { cn } from "@/utils/cn";

interface ActionBadgeProps {
  action: Action;
  size?: "sm" | "md";
  showLabel?: boolean;
}

/**
 * Cooperate/Defect indicator.
 *
 * Colour is never the only signal: every badge carries both an icon and a
 * text label, so the meaning survives greyscale printing and colour-vision
 * differences alike.
 */
export function ActionBadge({ action, size = "sm", showLabel = true }: ActionBadgeProps) {
  const cooperates = action === "COOPERATE";
  const Icon = cooperates ? Handshake : Swords;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md font-medium ring-1 ring-inset",
        cooperates
          ? "bg-cooperate-soft text-emerald-200 ring-emerald-400/40"
          : "bg-defect-soft text-rose-200 ring-red-300",
        size === "sm" ? "px-1.5 py-0.5 text-xs" : "px-2.5 py-1 text-sm",
      )}
    >
      <Icon className={size === "sm" ? "h-3 w-3" : "h-4 w-4"} aria-hidden />
      {showLabel ? (cooperates ? "Cooperate" : "Defect") : <span className="sr-only">{cooperates ? "Cooperate" : "Defect"}</span>}
      {!showLabel ? <span aria-hidden>{cooperates ? "C" : "D"}</span> : null}
    </span>
  );
}
