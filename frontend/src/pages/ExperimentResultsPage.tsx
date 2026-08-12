import { useParams } from "react-router-dom";
import { BarChart3, Download } from "lucide-react";
import { experimentApi } from "@/api/experimentApi";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { SkeletonStats } from "@/components/common/Skeleton";
import { StatCard } from "@/components/common/StatCard";
import { ChartFrame } from "@/components/charts/ChartFrame";
import {
  CategoryBarChart,
  MultiLineChart,
  OutcomePieChart,
} from "@/components/charts/Charts";
import { PageHeader } from "@/components/layout/PageHeader";
import { useApiAction, useExperiment, useStatistics } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import { formatNumber, formatPercent } from "@/utils/format";
import { downloadBlob } from "@/utils/download";
import { CHART_COLORS, OUTCOME_COLORS, OUTCOME_LABELS, OUTCOME_ORDER } from "@/utils/game";

/** Aggregated results of one classroom experiment. */
export function ExperimentResultsPage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();

  const experiment = useExperiment(id);
  const statistics = useStatistics("experiment", id);
  const exportAction = useApiAction(experimentApi.exportRoundsCsv);

  const exportCsv = async () => {
    if (!id) return;
    const blob = await exportAction.execute(id);
    if (blob) {
      downloadBlob(blob, `experiment-${id}-rounds.csv`);
      toast.success("Download started", "Round data exported as CSV.");
    } else if (exportAction.error) {
      toast.apiError(exportAction.error, "Export failed");
    }
  };

  if (statistics.loading || experiment.loading) {
    return (
      <>
        <PageHeader title="Experiment results" icon={<BarChart3 className="h-5 w-5" />} />
        <SkeletonStats count={4} />
      </>
    );
  }

  if (statistics.error) {
    return (
      <>
        <PageHeader title="Experiment results" icon={<BarChart3 className="h-5 w-5" />} />
        <Card>
          <ErrorState error={statistics.error} onRetry={statistics.refresh} />
        </Card>
      </>
    );
  }

  const stats = statistics.data;
  const detail = experiment.data;

  if (!stats || !detail) return null;

  if (stats.rounds_recorded === 0) {
    return (
      <>
        <PageHeader
          title="Experiment results"
          icon={<BarChart3 className="h-5 w-5" />}
          breadcrumbs={[
            { label: "Experiments", to: "/experiments" },
            { label: detail.name, to: `/experiments/${detail.id}` },
            { label: "Results" },
          ]}
        />
        <Card>
          <EmptyState
            icon={<BarChart3 className="h-6 w-6" />}
            title="No rounds recorded yet"
            description="Record some rounds on the play screen and the analysis will appear here."
          />
        </Card>
      </>
    );
  }

  const cooperationByRound = stats.cooperation_rate_by_round.map((row) => ({
    round: row.round_number,
    cooperation: row.cooperation_rate ?? 0,
    defection: 1 - (row.cooperation_rate ?? 0),
  }));

  const payoffByRound = stats.payoff_by_round.map((row) => ({
    label: String(row.round_number),
    value: row.average_payoff ?? 0,
  }));

  const outcomeSlices = OUTCOME_ORDER.map((outcome) => ({
    label: `${outcome} — ${OUTCOME_LABELS[outcome]}`,
    value: stats.outcome_frequency[outcome] ?? 0,
    color: OUTCOME_COLORS[outcome],
  }));

  return (
    <>
      <PageHeader
        title="Experiment results"
        description={detail.name}
        icon={<BarChart3 className="h-5 w-5" />}
        breadcrumbs={[
          { label: "Experiments", to: "/experiments" },
          { label: detail.name, to: `/experiments/${detail.id}` },
          { label: "Results" },
        ]}
        actions={
          <Button
            variant="secondary"
            size="sm"
            icon={<Download className="h-4 w-4" />}
            loading={exportAction.pending}
            onClick={exportCsv}
          >
            Export CSV
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Participants" value={detail.participant_count} />
        <StatCard label="Rounds recorded" value={stats.rounds_recorded} />
        <StatCard
          label="Cooperation rate"
          value={formatPercent(stats.cooperation_rate)}
          tone="cooperate"
          hint="Share of all individual decisions that were Cooperate."
        />
        <StatCard
          label="Defection rate"
          value={formatPercent(stats.defection_rate)}
          tone="defect"
        />
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Mutual cooperation"
          value={formatPercent(stats.mutual_cooperation_rate)}
          hint="Rounds where both players cooperated."
        />
        <StatCard
          label="Mutual defection"
          value={formatPercent(stats.mutual_defection_rate)}
          hint="Rounds where both players defected — the Nash equilibrium outcome of the classic matrix."
        />
        <StatCard label="Average payoff" value={formatNumber(stats.average_payoff)} />
        <StatCard
          label="Total payoff"
          value={formatNumber(stats.total_payoff, 0)}
          footer={`${stats.decisions_recorded} decisions`}
        />
      </div>

      {stats.nash_prediction_applies ? (
        <Card className="mt-4">
          <CardHeader
            title="Observed behaviour versus the Nash prediction"
            description="What the theory predicts, next to what the class actually did"
          />
          <CardBody>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-lab-250 p-3">
                <p className="text-xs tracking-wide text-lab-600 uppercase">Predicted</p>
                <p className="mt-1 text-xl font-semibold text-lab-900">
                  {formatPercent(stats.nash_prediction_cooperation_rate)}
                </p>
                <p className="text-xs text-lab-600">
                  cooperation, if every player plays the one-shot equilibrium
                </p>
              </div>
              <div className="rounded-lg border border-lab-250 p-3">
                <p className="text-xs tracking-wide text-lab-600 uppercase">Observed</p>
                <p className="mt-1 text-xl font-semibold text-emerald-300">
                  {formatPercent(stats.cooperation_rate)}
                </p>
                <p className="text-xs text-lab-600">actual cooperation in this session</p>
              </div>
              <div className="rounded-lg border border-lab-250 p-3">
                <p className="text-xs tracking-wide text-lab-600 uppercase">Difference</p>
                <p className="mt-1 text-xl font-semibold text-violet-300">
                  {formatPercent(
                    stats.cooperation_rate - stats.nash_prediction_cooperation_rate,
                  )}
                </p>
                <p className="text-xs text-lab-600">observed minus predicted</p>
              </div>
            </div>
            <p className="mt-3 rounded-lg bg-lab-50 p-3 text-xs leading-relaxed text-lab-700">
              Cooperation above the prediction means play departed from the one-shot
              equilibrium. Repeated interaction gives players a reason to build and
              protect a cooperative record. This is a description of one small sample, not
              evidence of a general law.
            </p>
          </CardBody>
        </Card>
      ) : (
        <Card className="mt-4">
          <CardBody>
            <p className="text-sm text-lab-700">
              This experiment&apos;s payoff matrix does not have mutual defection as its
              unique equilibrium, so the standard &quot;0% cooperation&quot; prediction
              does not apply here.
            </p>
          </CardBody>
        </Card>
      )}

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <ChartFrame
          title="Cooperation by round"
          description="Share of players cooperating in each round"
          hint="A downward trend towards the final round is the end-game effect: with fewer future rounds to protect, defection becomes safer."
        >
          <MultiLineChart
            data={cooperationByRound}
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

        <ChartFrame
          title="Average payoff by round"
          description="Mean points earned per decision"
        >
          <CategoryBarChart
            data={payoffByRound}
            xLabel="Round"
            yLabel="Average payoff"
            color={CHART_COLORS.accent}
            formatter={(value) => value.toFixed(2)}
          />
        </ChartFrame>

        <ChartFrame
          title="Outcome distribution"
          description="How the rounds split across the four cells"
        >
          <OutcomePieChart data={outcomeSlices} />
        </ChartFrame>

        <Card>
          <CardHeader title="Outcome breakdown" />
          <CardBody>
            <dl className="space-y-2">
              {OUTCOME_ORDER.map((outcome) => {
                const rate =
                  outcome === "CC"
                    ? stats.mutual_cooperation_rate
                    : outcome === "DD"
                      ? stats.mutual_defection_rate
                      : outcome === "CD"
                        ? stats.cd_rate
                        : stats.dc_rate;
                return (
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
                    <dd className="text-right">
                      <span className="font-mono text-sm font-semibold text-lab-900">
                        {stats.outcome_frequency[outcome] ?? 0}
                      </span>
                      <span className="ml-2 font-mono text-xs text-lab-600">
                        {formatPercent(rate)}
                      </span>
                    </dd>
                  </div>
                );
              })}
            </dl>
          </CardBody>
        </Card>
      </div>
    </>
  );
}
