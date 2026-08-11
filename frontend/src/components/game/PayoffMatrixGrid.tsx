import { Crown, Target } from "lucide-react";
import type { GameAnalysis, Outcome, PayoffMatrixInput } from "@/types";
import { cn } from "@/utils/cn";
import { OUTCOME_LABELS } from "@/utils/game";

interface PayoffMatrixGridProps {
  matrix: PayoffMatrixInput;
  /** Backend analysis. Badges are only drawn from this, never inferred here. */
  analysis?: GameAnalysis | null;
  editable?: boolean;
  onCellChange?: (outcome: Outcome, player: "a" | "b", value: number) => void;
  onCellClick?: (outcome: Outcome) => void;
  selected?: Outcome | null;
}

const CELL_ORDER: Array<{ outcome: Outcome; row: number; column: number }> = [
  { outcome: "CC", row: 0, column: 0 },
  { outcome: "CD", row: 0, column: 1 },
  { outcome: "DC", row: 1, column: 0 },
  { outcome: "DD", row: 1, column: 1 },
];

/**
 * The 2x2 payoff matrix, optionally editable.
 *
 * Nash and Pareto badges come straight from the backend's analysis of the
 * matrix currently on screen — the classic result is never assumed, so a
 * custom matrix shows its own equilibrium wherever that happens to be.
 */
export function PayoffMatrixGrid({
  matrix,
  analysis,
  editable = false,
  onCellChange,
  onCellClick,
  selected,
}: PayoffMatrixGridProps) {
  const nashOutcomes = new Set(analysis?.nash_equilibria.map((eq) => eq.outcome) ?? []);
  const paretoOptimal = new Set(analysis?.pareto_optimal_outcomes ?? []);

  return (
    <div className="overflow-x-auto">
      <div className="inline-grid min-w-[22rem] grid-cols-[auto_1fr_1fr] gap-2">
        <div aria-hidden />
        <div className="pb-1 text-center text-xs font-semibold tracking-wide text-slate-500 uppercase">
          B: Cooperate
        </div>
        <div className="pb-1 text-center text-xs font-semibold tracking-wide text-slate-500 uppercase">
          B: Defect
        </div>

        {["Cooperate", "Defect"].map((rowLabel, rowIndex) => (
          <div key={rowLabel} className="contents">
            <div className="flex items-center pr-2 text-xs font-semibold tracking-wide text-slate-500 uppercase">
              <span className="[writing-mode:vertical-rl] rotate-180 sm:writing-mode-horizontal sm:rotate-0">
                A: {rowLabel}
              </span>
            </div>

            {CELL_ORDER.filter((cell) => cell.row === rowIndex).map((cell) => {
              const values = matrix[cell.outcome.toLowerCase() as keyof PayoffMatrixInput];
              const isNash = nashOutcomes.has(cell.outcome);
              const isOptimal = paretoOptimal.has(cell.outcome);
              const isSelected = selected === cell.outcome;

              return (
                <div
                  key={cell.outcome}
                  onClick={onCellClick ? () => onCellClick(cell.outcome) : undefined}
                  onKeyDown={
                    onCellClick
                      ? (event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            onCellClick(cell.outcome);
                          }
                        }
                      : undefined
                  }
                  role={onCellClick ? "button" : undefined}
                  tabIndex={onCellClick ? 0 : undefined}
                  aria-label={`${OUTCOME_LABELS[cell.outcome]}: player A ${values.player_a_payoff}, player B ${values.player_b_payoff}`}
                  className={cn(
                    "relative rounded-xl border-2 p-4 transition-all",
                    onCellClick && "cursor-pointer hover:border-indigo-400 hover:shadow-md",
                    isSelected ? "border-indigo-500 bg-indigo-50/60" : "border-lab-200 bg-white",
                  )}
                >
                  <div className="mb-2 flex flex-wrap items-center gap-1">
                    <span className="rounded bg-lab-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-lab-600">
                      {cell.outcome}
                    </span>
                    {isNash ? (
                      <span
                        title="Nash equilibrium, as computed by the backend"
                        className="inline-flex items-center gap-0.5 rounded bg-indigo-100 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-800"
                      >
                        <Target className="h-3 w-3" aria-hidden />
                        Nash
                      </span>
                    ) : null}
                    {isOptimal ? (
                      <span
                        title="Pareto-optimal, as computed by the backend"
                        className="inline-flex items-center gap-0.5 rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-800"
                      >
                        <Crown className="h-3 w-3" aria-hidden />
                        Pareto
                      </span>
                    ) : null}
                  </div>

                  {editable ? (
                    <div className="flex items-center justify-center gap-1.5">
                      <input
                        type="number"
                        value={values.player_a_payoff}
                        aria-label={`Player A payoff for ${cell.outcome}`}
                        onClick={(event) => event.stopPropagation()}
                        onChange={(event) =>
                          onCellChange?.(cell.outcome, "a", Number(event.target.value))
                        }
                        className="w-16 rounded-lg border border-lab-300 px-2 py-1.5 text-center font-mono text-sm text-blue-700 focus:border-indigo-500"
                      />
                      <span className="text-slate-400" aria-hidden>
                        ,
                      </span>
                      <input
                        type="number"
                        value={values.player_b_payoff}
                        aria-label={`Player B payoff for ${cell.outcome}`}
                        onClick={(event) => event.stopPropagation()}
                        onChange={(event) =>
                          onCellChange?.(cell.outcome, "b", Number(event.target.value))
                        }
                        className="w-16 rounded-lg border border-lab-300 px-2 py-1.5 text-center font-mono text-sm text-orange-700 focus:border-indigo-500"
                      />
                    </div>
                  ) : (
                    <p className="text-center font-mono text-xl font-semibold text-lab-900">
                      <span className="text-blue-700">{values.player_a_payoff}</span>
                      <span className="text-slate-400">, </span>
                      <span className="text-orange-700">{values.player_b_payoff}</span>
                    </p>
                  )}

                  <p className="mt-2 text-center text-[11px] text-slate-500">
                    {OUTCOME_LABELS[cell.outcome]}
                  </p>
                </div>
              );
            })}
          </div>
        ))}
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Each cell shows <span className="font-medium text-blue-700">Player A&apos;s payoff</span>,{" "}
        <span className="font-medium text-orange-700">Player B&apos;s payoff</span>.
      </p>
    </div>
  );
}
