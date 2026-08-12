import type { ReactNode } from "react";
import { BookOpen } from "lucide-react";

interface ConceptCardProps {
  term: string;
  definition: string;
  children?: ReactNode;
}

/**
 * A plain-language definition of one game-theory term, for readers meeting it
 * for the first time.
 */
export function ConceptCard({ term, definition, children }: ConceptCardProps) {
  return (
    <div className="rounded-xl border border-violet-500/20 bg-violet-500/10 p-4">
      <div className="flex items-start gap-2.5">
        <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" aria-hidden />
        <div>
          <h4 className="text-sm font-semibold text-violet-100">{term}</h4>
          <p className="mt-1 text-sm leading-relaxed text-lab-800">{definition}</p>
          {children ? <div className="mt-2">{children}</div> : null}
        </div>
      </div>
    </div>
  );
}

/** The shared glossary, so wording stays identical everywhere it appears. */
export const CONCEPTS = {
  dominantStrategy: {
    term: "Dominant strategy",
    definition:
      "A strategy that gives a player a better payoff regardless of what the other player does.",
  },
  nashEquilibrium: {
    term: "Nash equilibrium",
    definition:
      "A situation where no player can improve their payoff by changing strategy alone.",
  },
  paretoInferior: {
    term: "Pareto inferior",
    definition:
      "An outcome where both players could be better off under another outcome.",
  },
  paretoOptimal: {
    term: "Pareto optimal",
    definition:
      "An outcome where no player can be made better off without making the other worse off.",
  },
  repeatedGame: {
    term: "Repeated game",
    definition:
      "The game is played multiple times, so current actions can affect future interactions.",
  },
  shadowOfTheFuture: {
    term: "Shadow of the future",
    definition:
      "When players expect to meet again, the value of future rounds can change what they do today.",
  },
  temptation: {
    term: "Temptation payoff (T)",
    definition: "What a player earns by defecting against someone who cooperates.",
  },
  reward: {
    term: "Reward payoff (R)",
    definition: "What each player earns when both cooperate.",
  },
  punishment: {
    term: "Punishment payoff (P)",
    definition: "What each player earns when both defect.",
  },
  sucker: {
    term: "Sucker's payoff (S)",
    definition: "What a player earns by cooperating with someone who defects.",
  },
} as const;
