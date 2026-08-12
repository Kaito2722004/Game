import { AlertTriangle, Check, Crown, Scale, Target, X } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { InfoTooltip } from "@/components/common/InfoTooltip";
import type { GameAnalysis, PayoffOrdering } from "@/types";
import { OUTCOME_LABELS } from "@/utils/game";

/**
 * Panels that display one backend `GameAnalysis`.
 *
 * These components render results only. No dominance, equilibrium or Pareto
 * conclusion is derived here — every claim on screen came from the API.
 */

export function ConditionsPanel({ analysis }: { analysis: GameAnalysis }) {
  const { conditions } = analysis;
  const isPD = conditions.is_prisoners_dilemma;

  return (
    <Card>
      <CardHeader
        title="Prisoner's Dilemma conditions"
        description="Checked against the payoff numbers by the backend"
        icon={<Scale className="h-5 w-5" />}
        actions={
          isPD ? (
            <Badge tone="success" icon={<Check className="h-3 w-3" aria-hidden />}>
              Is a Prisoner&apos;s Dilemma
            </Badge>
          ) : (
            <Badge tone="warning" icon={<AlertTriangle className="h-3 w-3" aria-hidden />}>
              Not a Prisoner&apos;s Dilemma
            </Badge>
          )
        }
      />
      <CardBody className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <OrderingCard label="Player A" ordering={conditions.player_a} />
          <OrderingCard label="Player B" ordering={conditions.player_b} />
        </div>

        <div className="space-y-2">
          <ConditionRow
            label="T > R > P > S"
            holds={conditions.ordering_holds}
            explanation="Defecting must be tempting, mutual cooperation must beat mutual defection, and being exploited must be worst."
          />
          <ConditionRow
            label="R > (S + T) / 2"
            holds={conditions.averaging_condition_holds}
            explanation="Steady mutual cooperation must beat taking turns exploiting each other."
          />
        </div>

        {conditions.failed_conditions.length > 0 ? (
          <ul className="space-y-1 rounded-lg bg-amber-400/10 p-3 text-xs text-amber-200">
            {conditions.failed_conditions.map((reason, index) => (
              <li key={index}>{reason}</li>
            ))}
          </ul>
        ) : null}

        {!conditions.is_symmetric ? (
          <p className="rounded-lg bg-sky-500/10 p-3 text-xs text-sky-200">
            This matrix is asymmetric: the two players face different payoffs, so their
            T, R, P and S values differ.
          </p>
        ) : null}
      </CardBody>
    </Card>
  );
}

function OrderingCard({ label, ordering }: { label: string; ordering: PayoffOrdering }) {
  const values: Array<{ symbol: string; name: string; value: number }> = [
    { symbol: "T", name: "Temptation", value: ordering.temptation },
    { symbol: "R", name: "Reward", value: ordering.reward },
    { symbol: "P", name: "Punishment", value: ordering.punishment },
    { symbol: "S", name: "Sucker", value: ordering.sucker },
  ];

  return (
    <div className="rounded-lg border border-lab-250 p-3">
      <p className="mb-2 text-xs font-semibold tracking-wide text-lab-600 uppercase">
        {label}
      </p>
      <dl className="grid grid-cols-4 gap-2">
        {values.map((entry) => (
          <div key={entry.symbol} className="text-center">
            <dt className="text-[11px] text-lab-600" title={entry.name}>
              {entry.symbol}
            </dt>
            <dd className="font-mono text-lg font-semibold text-lab-900">{entry.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function ConditionRow({
  label,
  holds,
  explanation,
}: {
  label: string;
  holds: boolean;
  explanation: string;
}) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-lab-250 px-3 py-2">
      <span
        className={
          holds ? "mt-0.5 rounded-full bg-emerald-400/15 p-1" : "mt-0.5 rounded-full bg-rose-500/15 p-1"
        }
        aria-hidden
      >
        {holds ? (
          <Check className="h-3 w-3 text-emerald-400" />
        ) : (
          <X className="h-3 w-3 text-rose-300" />
        )}
      </span>
      <div className="min-w-0">
        <p className="font-mono text-sm font-medium text-lab-900">
          {label}{" "}
          <span className={holds ? "text-emerald-400" : "text-rose-300"}>
            — {holds ? "holds" : "fails"}
          </span>
        </p>
        <p className="text-xs text-lab-700">{explanation}</p>
      </div>
    </div>
  );
}

export function DominancePanel({ analysis }: { analysis: GameAnalysis }) {
  const players = [
    { label: "Player A", dominant: analysis.dominant_strategy_player_a },
    { label: "Player B", dominant: analysis.dominant_strategy_player_b },
  ];

  return (
    <Card>
      <CardHeader
        title="Dominant strategy"
        description="An action that pays better whatever the opponent does"
        icon={<Crown className="h-5 w-5" />}
        actions={
          <InfoTooltip text="A strategy that gives a player a better payoff regardless of what the other player does." />
        }
      />
      <CardBody className="space-y-3">
        {players.map(({ label, dominant }) => (
          <div key={label} className="rounded-lg border border-lab-250 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-lab-900">{label}</span>
              {dominant.exists && dominant.action ? (
                <Badge tone={dominant.action === "COOPERATE" ? "cooperate" : "defect"}>
                  {dominant.action === "COOPERATE" ? "Cooperate" : "Defect"} dominates
                </Badge>
              ) : (
                <Badge tone="neutral">No dominant action</Badge>
              )}
              {dominant.dominance ? (
                <Badge tone="neutral">{dominant.dominance.toLowerCase()}</Badge>
              ) : null}
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-lab-700">
              {dominant.explanation}
            </p>
          </div>
        ))}
      </CardBody>
    </Card>
  );
}

export function NashPanel({ analysis }: { analysis: GameAnalysis }) {
  return (
    <Card>
      <CardHeader
        title="Nash equilibrium"
        description="Outcomes nobody can improve on by changing alone"
        icon={<Target className="h-5 w-5" />}
        actions={
          <InfoTooltip text="A situation where no player can improve their payoff by changing strategy alone." />
        }
      />
      <CardBody className="space-y-3">
        {analysis.nash_equilibria.length === 0 ? (
          <p className="text-sm text-lab-700">
            This matrix has no pure-strategy Nash equilibrium. Every cell gives at least
            one player a reason to switch.
          </p>
        ) : (
          analysis.nash_equilibria.map((equilibrium) => (
            <div
              key={equilibrium.outcome}
              className="rounded-lg border border-violet-500/30 bg-violet-500/10 p-3"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="accent" icon={<Target className="h-3 w-3" aria-hidden />}>
                  {equilibrium.outcome}
                </Badge>
                <span className="text-sm font-medium text-lab-900">
                  {OUTCOME_LABELS[equilibrium.outcome]}
                </span>
                <span className="font-mono text-sm text-lab-700">
                  ({equilibrium.player_a_payoff}, {equilibrium.player_b_payoff})
                </span>
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-lab-700">
                {equilibrium.explanation}
              </p>
            </div>
          ))
        )}
      </CardBody>
    </Card>
  );
}

export function ParetoPanel({ analysis }: { analysis: GameAnalysis }) {
  return (
    <Card>
      <CardHeader
        title="Pareto comparison"
        description="Which outcomes could be improved for someone at nobody's expense"
        icon={<Scale className="h-5 w-5" />}
        actions={
          <InfoTooltip text="An outcome is Pareto inferior when both players could be better off under another outcome." />
        }
      />
      <CardBody className="space-y-3">
        <div className="grid gap-2 sm:grid-cols-2">
          {analysis.pareto_analysis.map((status) => (
            <div
              key={status.outcome}
              className={
                status.is_pareto_optimal
                  ? "rounded-lg border border-emerald-400/30 bg-emerald-400/10 p-3"
                  : "rounded-lg border border-amber-400/30 bg-amber-400/10/40 p-3"
              }
            >
              <div className="flex items-center gap-2">
                <span className="rounded bg-lab-100 px-1.5 py-0.5 font-mono text-xs font-semibold text-lab-700">
                  {status.outcome}
                </span>
                <Badge tone={status.is_pareto_optimal ? "success" : "warning"}>
                  {status.is_pareto_optimal ? "Pareto optimal" : "Pareto inferior"}
                </Badge>
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-lab-700">
                {status.explanation}
              </p>
            </div>
          ))}
        </div>

        {analysis.equilibrium_is_pareto_inferior ? (
          <div className="rounded-lg border border-violet-500/30 bg-violet-500/10 p-3">
            <p className="text-sm font-medium text-violet-100">
              Individual rationality and collective benefit disagree here.
            </p>
            <p className="mt-1 text-xs leading-relaxed text-lab-800">
              At least one equilibrium of this matrix is Pareto inferior: the players end
              up somewhere they could both have improved on. That tension is what makes
              the Prisoner&apos;s Dilemma interesting.
            </p>
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

export function SummaryPanel({ analysis }: { analysis: GameAnalysis }) {
  return (
    <div className="rounded-xl border border-lab-250 bg-lab-100 p-4">
      <p className="text-sm leading-relaxed text-lab-800">{analysis.summary}</p>
      <p className="mt-2 text-xs text-lab-600">
        Computed by the backend from the matrix currently on screen.
      </p>
    </div>
  );
}
