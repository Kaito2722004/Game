import { Check, Eye, EyeOff, Handshake, Swords } from "lucide-react";
import { Button } from "@/components/common/Button";
import type { Action } from "@/types";
import { cn } from "@/utils/cn";

interface HiddenChoicePanelProps {
  playerLabel: string;
  choice: Action | null;
  onChoose: (action: Action) => void;
  /** While false the panel masks the choice so the opposite player cannot see it. */
  revealed: boolean;
  disabled?: boolean;
}

/**
 * One player's private choice.
 *
 * The whole point of the Prisoner's Dilemma is that the two decisions are
 * simultaneous, so until both are locked in the panel shows only that a choice
 * has been made — never which one. On a shared screen the second player can
 * look at the first player's panel and learn nothing.
 */
export function HiddenChoicePanel({
  playerLabel,
  choice,
  onChoose,
  revealed,
  disabled = false,
}: HiddenChoicePanelProps) {
  const chosen = choice !== null;

  return (
    <div
      className={cn(
        "rounded-xl border-2 p-5 transition-colors",
        revealed && chosen
          ? choice === "COOPERATE"
            ? "border-green-300 bg-cooperate-soft"
            : "border-red-300 bg-defect-soft"
          : chosen
            ? "border-violet-500/50 bg-violet-500/10"
            : "border-lab-250 bg-lab-100",
      )}
    >
      <div className="mb-4 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-lab-950">{playerLabel}</h3>
        {chosen ? (
          revealed ? (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-lab-700">
              <Eye className="h-3.5 w-3.5" aria-hidden />
              Revealed
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-violet-300">
              <EyeOff className="h-3.5 w-3.5" aria-hidden />
              Choice hidden
            </span>
          )
        ) : (
          <span className="text-xs text-lab-600">Waiting for a choice</span>
        )}
      </div>

      {revealed && chosen ? (
        <div className="py-4 text-center">
          <span
            className={cn(
              "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-lg font-semibold",
              choice === "COOPERATE" ? "text-emerald-200" : "text-rose-200",
            )}
          >
            {choice === "COOPERATE" ? (
              <Handshake className="h-6 w-6" aria-hidden />
            ) : (
              <Swords className="h-6 w-6" aria-hidden />
            )}
            {choice === "COOPERATE" ? "Cooperate" : "Defect"}
          </span>
        </div>
      ) : chosen ? (
        <div className="flex flex-col items-center gap-2 py-6">
          <span className="rounded-full bg-violet-500/20 p-3 text-violet-300" aria-hidden>
            <Check className="h-6 w-6" />
          </span>
          <p className="text-sm font-medium text-violet-200">Locked in</p>
          <p className="text-center text-xs text-lab-600">
            The choice stays hidden until both players have decided.
          </p>
        </div>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2">
          <Button
            variant="cooperate"
            size="lg"
            icon={<Handshake className="h-4 w-4" />}
            onClick={() => onChoose("COOPERATE")}
            disabled={disabled}
            fullWidth
          >
            Cooperate
          </Button>
          <Button
            variant="defect"
            size="lg"
            icon={<Swords className="h-4 w-4" />}
            onClick={() => onChoose("DEFECT")}
            disabled={disabled}
            fullWidth
          >
            Defect
          </Button>
        </div>
      )}

      {chosen && !revealed ? (
        <div className="mt-3 flex justify-center">
          <Button variant="ghost" size="sm" onClick={() => onChoose(choice)} disabled>
            <span className="text-xs text-lab-600">Choice recorded</span>
          </Button>
        </div>
      ) : null}
    </div>
  );
}
