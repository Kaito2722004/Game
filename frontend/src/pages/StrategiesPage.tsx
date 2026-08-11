import { Handshake, Shield, Shuffle, Swords } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/common/Skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { useStrategies } from "@/hooks";
import type { Strategy, StrategyCategory } from "@/types";

const CATEGORY_META: Record<
  StrategyCategory,
  { label: string; tone: "cooperate" | "defect" | "info"; description: string }
> = {
  NICE: {
    label: "Nice",
    tone: "cooperate",
    description: "Never defects first",
  },
  NASTY: {
    label: "Nasty",
    tone: "defect",
    description: "Opens with defection",
  },
  STOCHASTIC: {
    label: "Stochastic",
    tone: "info",
    description: "Uses randomness",
  },
};

/**
 * Worked example of how each strategy behaves against Always Defect, so the
 * rule becomes concrete. These illustrate the documented rule; actual match
 * results always come from the simulator.
 */
const EXAMPLES: Record<string, { situation: string; behaviour: string }> = {
  ALWAYS_COOPERATE: {
    situation: "Opponent defects every round",
    behaviour: "Keeps cooperating and is exploited in every round.",
  },
  ALWAYS_DEFECT: {
    situation: "Opponent cooperates every round",
    behaviour: "Keeps defecting and takes the temptation payoff every round.",
  },
  TIT_FOR_TAT: {
    situation: "Opponent defects in round 3",
    behaviour: "Cooperates through round 3, defects in round 4, then returns to cooperation as soon as the opponent does.",
  },
  GRIM_TRIGGER: {
    situation: "Opponent defects once in round 3",
    behaviour: "Cooperates through round 3, then defects in every remaining round no matter what the opponent does.",
  },
  TIT_FOR_TWO_TATS: {
    situation: "Opponent defects once, then cooperates",
    behaviour: "Ignores the isolated defection and keeps cooperating. It only retaliates after two defections in a row.",
  },
  RANDOM: {
    situation: "Any opponent",
    behaviour: "Ignores the history entirely and flips a fair coin each round.",
  },
};

function categoryIcon(category: StrategyCategory) {
  if (category === "NICE") return <Handshake className="h-4 w-4" aria-hidden />;
  if (category === "NASTY") return <Swords className="h-4 w-4" aria-hidden />;
  return <Shuffle className="h-4 w-4" aria-hidden />;
}

function StrategyCard({ strategy }: { strategy: Strategy }) {
  const meta = CATEGORY_META[strategy.category];
  const example = EXAMPLES[strategy.id];

  return (
    <Card className="flex flex-col transition-shadow hover:shadow-md">
      <CardHeader
        title={strategy.name}
        icon={categoryIcon(strategy.category)}
        actions={
          <div className="flex flex-wrap justify-end gap-1">
            <Badge tone={meta.tone} title={meta.description}>
              {meta.label}
            </Badge>
            <Badge tone="neutral">
              {strategy.is_deterministic ? "Deterministic" : "Random"}
            </Badge>
          </div>
        }
      />
      <CardBody className="flex flex-1 flex-col gap-4">
        <p className="text-sm leading-relaxed text-slate-700">{strategy.description}</p>

        <div>
          <h4 className="mb-1.5 text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Rule
          </h4>
          <ol className="list-inside list-decimal space-y-1 rounded-lg bg-lab-50 p-3 text-sm text-lab-800">
            {strategy.rules.map((rule, index) => (
              <li key={index}>{rule}</li>
            ))}
          </ol>
        </div>

        {example ? (
          <div className="mt-auto">
            <h4 className="mb-1.5 text-xs font-semibold tracking-wide text-slate-500 uppercase">
              Example
            </h4>
            <p className="text-xs text-slate-600">
              <span className="font-medium text-lab-800">{example.situation}: </span>
              {example.behaviour}
            </p>
          </div>
        ) : null}

        <p className="font-mono text-[11px] text-slate-400">{strategy.id}</p>
      </CardBody>
    </Card>
  );
}

export function StrategiesPage() {
  const { data, loading, error, refresh } = useStrategies();

  return (
    <>
      <PageHeader
        title="Strategies"
        description="The rules the simulation engine can play. This list comes from the backend's strategy registry, so it always matches what the tournament can run."
        icon={<Shield className="h-5 w-5" />}
      />

      {error ? (
        <Card>
          <ErrorState error={error} onRetry={refresh} />
        </Card>
      ) : null}

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-72 w-full" />
          ))}
        </div>
      ) : null}

      {data && data.length === 0 ? (
        <Card>
          <EmptyState
            title="No strategies registered"
            description="The backend returned an empty strategy registry."
          />
        </Card>
      ) : null}

      {data && data.length > 0 ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {data.map((strategy) => (
              <StrategyCard key={strategy.id} strategy={strategy} />
            ))}
          </div>

          <Card className="mt-6">
            <CardHeader
              title="What makes a strategy effective in repeated play"
              description="Four properties often discussed in Axelrod-style research"
            />
            <CardBody>
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  {
                    term: "Nice",
                    definition:
                      "Never defects first. A nice strategy can establish cooperation with anyone willing to reciprocate.",
                  },
                  {
                    term: "Retaliatory",
                    definition:
                      "Answers a defection promptly, so it cannot be exploited round after round.",
                  },
                  {
                    term: "Forgiving",
                    definition:
                      "Returns to cooperation once the opponent does, instead of feuding indefinitely.",
                  },
                  {
                    term: "Clear",
                    definition:
                      "Behaves predictably enough that an opponent can work out that cooperating pays.",
                  },
                ].map((entry) => (
                  <div key={entry.term} className="rounded-lg border border-lab-200 p-3">
                    <dt className="text-sm font-semibold text-lab-900">{entry.term}</dt>
                    <dd className="mt-1 text-xs leading-relaxed text-slate-600">
                      {entry.definition}
                    </dd>
                  </div>
                ))}
              </dl>

              <p className="mt-4 rounded-lg bg-amber-50 p-3 text-xs leading-relaxed text-amber-900">
                These properties describe tendencies, not a guarantee. No strategy here is
                universally optimal — how each one places depends on the payoff matrix and
                on which opponents it meets. The tournament decides the ranking, not this
                page.
              </p>
            </CardBody>
          </Card>
        </>
      ) : null}
    </>
  );
}
