import { useMemo, useState } from "react";
import { FlaskConical, Play, Trophy } from "lucide-react";
import { matchApi } from "@/api/matchApi";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { CheckboxField, SelectField, TextField } from "@/components/common/Field";
import { StatCard } from "@/components/common/StatCard";
import { ChartFrame } from "@/components/charts/ChartFrame";
import { MultiLineChart, OutcomePieChart } from "@/components/charts/Charts";
import { RoundHistoryTable } from "@/components/game/RoundHistoryTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { useApiAction, usePayoffMatrices, useStrategies } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import type { MatchResult } from "@/types";
import { formatNumber, formatPercent, humanizeCode } from "@/utils/format";
import { CHART_COLORS, OUTCOME_LABELS, OUTCOME_ORDER, OUTCOME_COLORS } from "@/utils/game";

/**
 * Run a single iterated match between two strategies.
 *
 * Every number displayed is returned by the backend; this page only arranges
 * it. Continuation probability is offered because it is the concrete way to
 * explore the shadow of the future.
 */
export function MatchSimulatorPage() {
  const strategies = useStrategies();
  const matrices = usePayoffMatrices();
  const toast = useToast();

  const [strategyA, setStrategyA] = useState("TIT_FOR_TAT");
  const [strategyB, setStrategyB] = useState("ALWAYS_DEFECT");
  const [rounds, setRounds] = useState(100);
  const [seed, setSeed] = useState<string>("42");
  const [useContinuation, setUseContinuation] = useState(false);
  const [continuation, setContinuation] = useState(0.95);
  const [matrixId, setMatrixId] = useState("");
  const [result, setResult] = useState<MatchResult | null>(null);

  const simulate = useApiAction(matchApi.simulate);

  const run = async () => {
    const response = await simulate.execute({
      strategy_a_id: strategyA,
      strategy_b_id: strategyB,
      rounds,
      seed: seed.trim() === "" ? null : Number(seed),
      continuation_probability: useContinuation ? continuation : null,
      payoff_matrix_id: matrixId || undefined,
    });

    if (response) {
      setResult(response);
      toast.success(
        "Simulation complete",
        `${response.rounds_played} rounds played.`,
      );
    } else if (simulate.error) {
      toast.apiError(simulate.error, "Simulation failed");
    }
  };

  const nameFor = (code: string) =>
    strategies.data?.find((item) => item.id === code)?.name ?? humanizeCode(code);

  const cumulativeData = useMemo(
    () =>
      (result?.cumulative_scores ?? []).map((point) => ({
        round: point.round_number,
        a: point.player_a_cumulative,
        b: point.player_b_cumulative,
      })),
    [result],
  );

  /**
   * Cooperation trend, smoothed over a window so the line is readable for
   * long matches. This is a display aggregation of backend round data, not a
   * recomputation of any result.
   */
  const cooperationTrend = useMemo(() => {
    const roundsList = result?.rounds ?? [];
    if (roundsList.length === 0) return [];
    const window = Math.max(1, Math.round(roundsList.length / 20));
    const points: Array<{ round: number; a: number; b: number }> = [];

    for (let start = 0; start < roundsList.length; start += window) {
      const slice = roundsList.slice(start, start + window);
      points.push({
        round: slice[0].round_number,
        a: slice.filter((r) => r.player_a_action === "COOPERATE").length / slice.length,
        b: slice.filter((r) => r.player_b_action === "COOPERATE").length / slice.length,
      });
    }
    return points;
  }, [result]);

  const outcomeData = useMemo(
    () =>
      OUTCOME_ORDER.map((outcome) => ({
        label: `${outcome} — ${OUTCOME_LABELS[outcome]}`,
        value: result?.outcome_counts[outcome] ?? 0,
        color: OUTCOME_COLORS[outcome],
      })),
    [result],
  );

  const strategyOptions = strategies.data ?? [];

  return (
    <>
      <PageHeader
        title="Match Simulator"
        description="Play two strategies against each other for a number of rounds and inspect every move."
        icon={<FlaskConical className="h-5 w-5" />}
      />

      <div className="grid gap-4 xl:grid-cols-[22rem_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader title="Setup" description="Choose the players and the conditions" />
          <CardBody className="space-y-4">
            {strategies.error ? (
              <ErrorState error={strategies.error} onRetry={strategies.refresh} />
            ) : (
              <>
                <SelectField
                  label="Player A strategy"
                  value={strategyA}
                  onChange={(event) => setStrategyA(event.target.value)}
                  disabled={strategies.loading}
                >
                  {strategyOptions.map((strategy) => (
                    <option key={strategy.id} value={strategy.id}>
                      {strategy.name}
                    </option>
                  ))}
                </SelectField>

                <SelectField
                  label="Player B strategy"
                  value={strategyB}
                  onChange={(event) => setStrategyB(event.target.value)}
                  disabled={strategies.loading}
                >
                  {strategyOptions.map((strategy) => (
                    <option key={strategy.id} value={strategy.id}>
                      {strategy.name}
                    </option>
                  ))}
                </SelectField>

                <TextField
                  label="Number of rounds"
                  type="number"
                  min={1}
                  max={10000}
                  value={rounds}
                  onChange={(event) => setRounds(Number(event.target.value))}
                  help="Between 1 and 10,000."
                />

                <SelectField
                  label="Payoff matrix"
                  value={matrixId}
                  onChange={(event) => setMatrixId(event.target.value)}
                >
                  <option value="">Backend default</option>
                  {(matrices.data ?? []).map((matrix) => (
                    <option key={matrix.id} value={matrix.id}>
                      {matrix.name}
                    </option>
                  ))}
                </SelectField>

                <TextField
                  label="Random seed"
                  type="number"
                  value={seed}
                  onChange={(event) => setSeed(event.target.value)}
                  hint="With a seed, the same run can be reproduced exactly. Only matters when a random strategy is involved."
                  help="Leave empty for an unseeded run."
                />

                <div className="space-y-2 rounded-lg border border-lab-250 p-3">
                  <CheckboxField
                    label="Uncertain ending"
                    description="After each round, another follows with the probability below."
                    checked={useContinuation}
                    onChange={(event) => setUseContinuation(event.target.checked)}
                  />
                  {useContinuation ? (
                    <div>
                      <label
                        htmlFor="continuation"
                        className="text-xs font-medium text-lab-700"
                      >
                        Continuation probability: {continuation.toFixed(2)}
                      </label>
                      <input
                        id="continuation"
                        type="range"
                        min={0}
                        max={1}
                        step={0.01}
                        value={continuation}
                        onChange={(event) => setContinuation(Number(event.target.value))}
                        className="mt-1 w-full accent-violet-500"
                      />
                      <p className="text-[11px] text-lab-600">
                        The round count above becomes an upper bound. This models the
                        shadow of the future: with no known last round, the
                        backward-induction argument has nowhere to start.
                      </p>
                    </div>
                  ) : null}
                </div>

                <Button
                  fullWidth
                  size="lg"
                  icon={<Play className="h-4 w-4" />}
                  loading={simulate.pending}
                  onClick={run}
                  disabled={strategies.loading || strategyOptions.length === 0}
                >
                  Run simulation
                </Button>
              </>
            )}
          </CardBody>
        </Card>

        <div className="space-y-4">
          {simulate.error && !result ? (
            <Card>
              <ErrorState error={simulate.error} onRetry={run} title="Simulation failed" />
            </Card>
          ) : null}

          {!result && !simulate.error ? (
            <Card>
              <EmptyState
                icon={<FlaskConical className="h-6 w-6" />}
                title="No simulation yet"
                description="Pick two strategies and run a match. Every round, payoff and total will be shown here."
              />
            </Card>
          ) : null}

          {result ? (
            <>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard
                  label={`${nameFor(result.strategy_a_id)} total`}
                  value={formatNumber(result.player_a.total_payoff, 0)}
                  footer={`Average ${formatNumber(result.player_a.average_payoff)} per round`}
                />
                <StatCard
                  label={`${nameFor(result.strategy_b_id)} total`}
                  value={formatNumber(result.player_b.total_payoff, 0)}
                  footer={`Average ${formatNumber(result.player_b.average_payoff)} per round`}
                />
                <StatCard
                  label="A cooperation rate"
                  value={formatPercent(result.player_a.cooperation_rate)}
                  tone="cooperate"
                  footer={`Defection ${formatPercent(result.player_a.defection_rate)}`}
                />
                <StatCard
                  label="B cooperation rate"
                  value={formatPercent(result.player_b.cooperation_rate)}
                  tone="cooperate"
                  footer={`Defection ${formatPercent(result.player_b.defection_rate)}`}
                />
              </div>

              <Card>
                <CardBody className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <Trophy className="h-5 w-5 text-violet-400" aria-hidden />
                    <span className="text-sm font-medium text-lab-900">
                      {result.is_draw
                        ? "The match was a draw."
                        : `${nameFor(result.winner ?? "")} scored higher.`}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge tone="neutral">{result.rounds_played} rounds played</Badge>
                    {result.seed !== null ? (
                      <Badge tone="neutral">seed {result.seed}</Badge>
                    ) : null}
                    {result.continuation_probability !== null ? (
                      <Badge tone="info">
                        continuation {result.continuation_probability}
                      </Badge>
                    ) : null}
                  </div>
                </CardBody>
              </Card>

              <div className="grid gap-4 xl:grid-cols-2">
                <ChartFrame
                  title="Cumulative payoff"
                  description="Running total for each player"
                  hint="Where the lines separate is where one strategy started pulling ahead."
                >
                  <MultiLineChart
                    data={cumulativeData}
                    xKey="round"
                    xLabel="Round"
                    yLabel="Cumulative payoff"
                    series={[
                      { key: "a", name: nameFor(result.strategy_a_id), color: CHART_COLORS.playerA },
                      { key: "b", name: nameFor(result.strategy_b_id), color: CHART_COLORS.playerB },
                    ]}
                  />
                </ChartFrame>

                <ChartFrame
                  title="Cooperation over the match"
                  description="Share of cooperative moves, averaged in blocks"
                  hint="Shows whether cooperation built up or broke down as the match went on."
                >
                  <MultiLineChart
                    data={cooperationTrend}
                    xKey="round"
                    xLabel="Round"
                    yLabel="Cooperation rate"
                    domain={[0, 1]}
                    formatter={(value) => formatPercent(value, 0)}
                    series={[
                      { key: "a", name: nameFor(result.strategy_a_id), color: CHART_COLORS.playerA },
                      { key: "b", name: nameFor(result.strategy_b_id), color: CHART_COLORS.playerB },
                    ]}
                  />
                </ChartFrame>

                <ChartFrame
                  title="Outcome distribution"
                  description="How the rounds were split between the four cells"
                >
                  <OutcomePieChart data={outcomeData} />
                </ChartFrame>

                <Card>
                  <CardHeader title="Outcome counts" />
                  <CardBody>
                    <dl className="space-y-2">
                      {OUTCOME_ORDER.map((outcome) => (
                        <div
                          key={outcome}
                          className="flex items-center justify-between gap-3 rounded-lg border border-lab-250 px-3 py-2"
                        >
                          <dt className="text-sm text-lab-800">
                            <span className="mr-2 rounded bg-lab-100 px-1.5 py-0.5 font-mono text-xs">
                              {outcome}
                            </span>
                            {OUTCOME_LABELS[outcome]}
                          </dt>
                          <dd className="font-mono text-sm font-semibold text-lab-900">
                            {result.outcome_counts[outcome] ?? 0}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </CardBody>
                </Card>
              </div>

              <Card>
                <CardHeader
                  title="Round-by-round history"
                  description="Every move and payoff, exactly as the backend recorded it"
                />
                <RoundHistoryTable
                  rounds={result.rounds}
                  labelA={nameFor(result.strategy_a_id)}
                  labelB={nameFor(result.strategy_b_id)}
                />
              </Card>
            </>
          ) : null}
        </div>
      </div>
    </>
  );
}
