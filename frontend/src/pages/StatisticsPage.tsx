import { useEffect, useState } from "react";
import { BarChart3 } from "lucide-react";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { SelectField } from "@/components/common/Field";
import { SkeletonStats } from "@/components/common/Skeleton";
import { StatCard } from "@/components/common/StatCard";
import { Tabs, type TabItem } from "@/components/common/Tabs";
import { ChartFrame } from "@/components/charts/ChartFrame";
import {
  CategoryBarChart,
  GroupedBarChart,
  MultiLineChart,
  OutcomePieChart,
} from "@/components/charts/Charts";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  useExperiments,
  useStatistics,
  useTournamentResults,
  useTournaments,
  useTrustSurveyStatistics,
} from "@/hooks";
import type { DescriptiveStatistics } from "@/types";
import { formatCorrelation, formatNumber, formatPercent } from "@/utils/format";
import { CHART_COLORS, OUTCOME_COLORS, OUTCOME_LABELS, OUTCOME_ORDER } from "@/utils/game";

const TABS: TabItem[] = [
  { id: "tournament", label: "Tournament" },
  { id: "experiment", label: "Human experiment" },
];

function StatisticsGrid({ stats }: { stats: DescriptiveStatistics }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-6">
      {[
        ["Count", String(stats.count)],
        ["Mean", formatNumber(stats.mean)],
        ["Median", formatNumber(stats.median)],
        ["Std deviation", formatNumber(stats.standard_deviation)],
        ["Minimum", formatNumber(stats.minimum)],
        ["Maximum", formatNumber(stats.maximum)],
      ].map(([label, value]) => (
        <div key={label} className="rounded-lg border border-lab-250 p-3">
          <p className="text-[11px] tracking-wide text-lab-600 uppercase">{label}</p>
          <p className="mt-0.5 font-mono text-lg font-semibold text-lab-900">{value}</p>
        </div>
      ))}
    </div>
  );
}

/** Research dashboard: descriptive statistics and charts for either study type. */
export function StatisticsPage() {
  const [tab, setTab] = useState("tournament");
  const [tournamentId, setTournamentId] = useState("");
  const [experimentId, setExperimentId] = useState("");

  const tournaments = useTournaments();
  const experiments = useExperiments();

  const completed = (tournaments.data ?? []).filter((item) => item.status === "COMPLETED");

  useEffect(() => {
    if (!tournamentId && completed.length > 0) setTournamentId(completed[0].id);
  }, [completed, tournamentId]);

  useEffect(() => {
    const list = experiments.data ?? [];
    if (!experimentId && list.length > 0) setExperimentId(list[0].id);
  }, [experiments.data, experimentId]);

  const tournamentStats = useStatistics("tournament", tournamentId, tab === "tournament");
  const tournamentResults = useTournamentResults(tournamentId, tab === "tournament");
  const experimentStats = useStatistics("experiment", experimentId, tab === "experiment");
  const surveyStats = useTrustSurveyStatistics(tab === "experiment" ? experimentId : undefined);

  return (
    <>
      <PageHeader
        title="Statistics"
        description="Descriptive statistics and charts, all computed by the backend."
        icon={<BarChart3 className="h-5 w-5" />}
      />

      <Tabs items={TABS} active={tab} onChange={setTab} className="mb-5" />

      {tab === "tournament" ? (
        <>
          <Card className="mb-4">
            <CardBody>
              <SelectField
                label="Tournament"
                value={tournamentId}
                onChange={(event) => setTournamentId(event.target.value)}
                help="Only completed tournaments have statistics."
              >
                <option value="">Select a tournament</option>
                {completed.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </SelectField>
            </CardBody>
          </Card>

          {completed.length === 0 ? (
            <Card>
              <EmptyState
                icon={<BarChart3 className="h-6 w-6" />}
                title="No completed tournaments"
                description="Run a tournament and its statistics will appear here."
              />
            </Card>
          ) : null}

          {tournamentStats.loading ? <SkeletonStats count={4} /> : null}
          {tournamentStats.error ? (
            <Card>
              <ErrorState error={tournamentStats.error} onRetry={tournamentStats.refresh} />
            </Card>
          ) : null}

          {tournamentStats.data ? (
            <div className="space-y-4">
              <Card>
                <CardHeader
                  title="Score distribution across strategies"
                  description="Descriptive statistics over each strategy's total score"
                />
                <CardBody>
                  <StatisticsGrid stats={tournamentStats.data.score_statistics} />
                </CardBody>
              </Card>

              <Card>
                <CardHeader
                  title="Cooperation rate distribution"
                  description="Descriptive statistics over each strategy's cooperation rate"
                />
                <CardBody>
                  <StatisticsGrid stats={tournamentStats.data.cooperation_rate_statistics} />
                </CardBody>
              </Card>

              <div className="grid gap-4 xl:grid-cols-2">
                {tournamentResults.data ? (
                  <>
                    <ChartFrame title="Strategy ranking" description="Total score">
                      <CategoryBarChart
                        data={tournamentResults.data.rankings.map((row) => ({
                          label: row.strategy_id,
                          value: row.total_score,
                        }))}
                        xLabel="Strategy"
                        yLabel="Total score"
                        color={CHART_COLORS.neutral}
                      />
                    </ChartFrame>

                    <ChartFrame title="Payoff comparison" description="Average per round">
                      <CategoryBarChart
                        data={tournamentResults.data.rankings.map((row) => ({
                          label: row.strategy_id,
                          value: row.average_score,
                        }))}
                        xLabel="Strategy"
                        yLabel="Average payoff"
                        color={CHART_COLORS.accent}
                        formatter={(value) => value.toFixed(2)}
                      />
                    </ChartFrame>

                    <ChartFrame
                      title="Cooperation and defection rates"
                      description="Share of each strategy's moves"
                    >
                      <GroupedBarChart
                        data={tournamentResults.data.rankings.map((row) => ({
                          label: row.strategy_id,
                          Cooperation: row.cooperation_rate,
                          Defection: row.defection_rate,
                        }))}
                        xKey="label"
                        xLabel="Strategy"
                        yLabel="Share of moves"
                        domain={[0, 1]}
                        formatter={(value) => formatPercent(value, 0)}
                        series={[
                          { key: "Cooperation", name: "Cooperate", color: CHART_COLORS.cooperate },
                          { key: "Defection", name: "Defect", color: CHART_COLORS.defect },
                        ]}
                      />
                    </ChartFrame>
                  </>
                ) : null}

                <ChartFrame
                  title="Outcome distribution"
                  description="Across every round of every match"
                >
                  <OutcomePieChart
                    data={OUTCOME_ORDER.map((outcome) => ({
                      label: `${outcome} — ${OUTCOME_LABELS[outcome]}`,
                      value: tournamentStats.data?.outcome_frequency[outcome] ?? 0,
                      color: OUTCOME_COLORS[outcome],
                    }))}
                  />
                </ChartFrame>

                {tournamentStats.data.cooperation_by_round.length > 0 ? (
                  <ChartFrame
                    title="Cooperation by round"
                    description="Pooled across all matches"
                  >
                    <MultiLineChart
                      data={tournamentStats.data.cooperation_by_round.map((row) => ({
                        round: row.round_number,
                        rate: row.cooperation_rate,
                      }))}
                      xKey="round"
                      xLabel="Round"
                      yLabel="Cooperation rate"
                      domain={[0, 1]}
                      formatter={(value) => formatPercent(value, 0)}
                      series={[
                        { key: "rate", name: "Cooperation rate", color: CHART_COLORS.cooperate },
                      ]}
                    />
                  </ChartFrame>
                ) : null}
              </div>
            </div>
          ) : null}
        </>
      ) : null}

      {tab === "experiment" ? (
        <>
          <Card className="mb-4">
            <CardBody>
              <SelectField
                label="Experiment"
                value={experimentId}
                onChange={(event) => setExperimentId(event.target.value)}
              >
                <option value="">Select an experiment</option>
                {(experiments.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </SelectField>
            </CardBody>
          </Card>

          {(experiments.data ?? []).length === 0 ? (
            <Card>
              <EmptyState
                icon={<BarChart3 className="h-6 w-6" />}
                title="No experiments"
                description="Create a classroom experiment to collect human data."
              />
            </Card>
          ) : null}

          {experimentStats.loading ? <SkeletonStats count={4} /> : null}
          {experimentStats.error ? (
            <Card>
              <ErrorState error={experimentStats.error} onRetry={experimentStats.refresh} />
            </Card>
          ) : null}

          {experimentStats.data && experimentStats.data.rounds_recorded > 0 ? (
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard
                  label="Cooperation rate"
                  value={formatPercent(experimentStats.data.cooperation_rate)}
                  tone="cooperate"
                />
                <StatCard
                  label="Defection rate"
                  value={formatPercent(experimentStats.data.defection_rate)}
                  tone="defect"
                />
                <StatCard
                  label="Mutual cooperation"
                  value={formatPercent(experimentStats.data.mutual_cooperation_rate)}
                />
                <StatCard
                  label="Mutual defection"
                  value={formatPercent(experimentStats.data.mutual_defection_rate)}
                />
              </div>

              <Card>
                <CardHeader
                  title="Payoff statistics"
                  description="Across every individual decision recorded"
                />
                <CardBody>
                  <StatisticsGrid stats={experimentStats.data.payoff_statistics} />
                </CardBody>
              </Card>

              <div className="grid gap-4 xl:grid-cols-2">
                <ChartFrame title="Cooperation by round" description="Human participants">
                  <MultiLineChart
                    data={experimentStats.data.cooperation_rate_by_round.map((row) => ({
                      round: row.round_number,
                      cooperation: row.cooperation_rate ?? 0,
                      defection: 1 - (row.cooperation_rate ?? 0),
                    }))}
                    xKey="round"
                    xLabel="Round"
                    yLabel="Rate"
                    domain={[0, 1]}
                    formatter={(value) => formatPercent(value, 0)}
                    series={[
                      { key: "cooperation", name: "Cooperate", color: CHART_COLORS.cooperate },
                      { key: "defection", name: "Defect", color: CHART_COLORS.defect },
                    ]}
                  />
                </ChartFrame>

                <ChartFrame title="Outcome distribution" description="Human rounds">
                  <OutcomePieChart
                    data={OUTCOME_ORDER.map((outcome) => ({
                      label: `${outcome} — ${OUTCOME_LABELS[outcome]}`,
                      value: experimentStats.data?.outcome_frequency[outcome] ?? 0,
                      color: OUTCOME_COLORS[outcome],
                    }))}
                  />
                </ChartFrame>
              </div>

              {surveyStats.data && surveyStats.data.responses > 0 ? (
                <Card>
                  <CardHeader
                    title="Trust and cooperation"
                    description="Survey answers next to observed behaviour"
                  />
                  <CardBody className="space-y-3">
                    <div className="grid gap-3 sm:grid-cols-3">
                      <StatCard
                        label="Expected cooperation"
                        value={formatNumber(surveyStats.data.average_expected_cooperation ?? 0, 2)}
                        footer="Mean of 1–5 answers before play"
                      />
                      <StatCard
                        label="Trust after play"
                        value={formatNumber(surveyStats.data.average_trust_after ?? 0, 2)}
                        footer="Mean of 1–5 answers after play"
                      />
                      <StatCard
                        label="Actual cooperation"
                        value={formatPercent(surveyStats.data.actual_cooperation_rate)}
                        tone="cooperate"
                      />
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-lg border border-lab-250 p-3">
                        <p className="text-xs text-lab-600">
                          Correlation: expected cooperation vs actual
                        </p>
                        <p className="font-mono text-lg font-semibold text-lab-900">
                          {formatCorrelation(surveyStats.data.correlation_expected_vs_actual)}
                        </p>
                      </div>
                      <div className="rounded-lg border border-lab-250 p-3">
                        <p className="text-xs text-lab-600">
                          Correlation: trust after vs actual
                        </p>
                        <p className="font-mono text-lg font-semibold text-lab-900">
                          {formatCorrelation(surveyStats.data.correlation_trust_after_vs_actual)}
                        </p>
                      </div>
                    </div>

                    <p className="rounded-lg bg-amber-400/10 p-3 text-xs leading-relaxed text-amber-200">
                      These are <strong>correlations</strong>, not causes. A relationship
                      between what people expected and what they did says nothing about
                      which produced the other, and a classroom sample is far too small to
                      support a psychological claim.
                    </p>
                  </CardBody>
                </Card>
              ) : null}
            </div>
          ) : null}

          {experimentStats.data && experimentStats.data.rounds_recorded === 0 ? (
            <Card>
              <EmptyState
                title="No rounds recorded"
                description="This experiment has no data yet."
              />
            </Card>
          ) : null}
        </>
      ) : null}
    </>
  );
}
