import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Download, ListOrdered, Play, Trophy } from "lucide-react";
import { tournamentApi } from "@/api/tournamentApi";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { DataTable, type Column } from "@/components/common/DataTable";
import { Dialog } from "@/components/common/Dialog";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { SkeletonStats, SkeletonTable } from "@/components/common/Skeleton";
import { StatCard } from "@/components/common/StatCard";
import { ChartFrame } from "@/components/charts/ChartFrame";
import { CategoryBarChart, GroupedBarChart, MultiLineChart } from "@/components/charts/Charts";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  useApiAction,
  useStatistics,
  useTournament,
  useTournamentResults,
} from "@/hooks";
import { useToast } from "@/context/ToastContext";
import { RequireRole } from "@/features/auth/RequireRole";
import { StatusBadge } from "@/features/tournament/StatusBadge";
import type { TournamentRanking } from "@/types";
import { formatNumber, formatPercent, formatScore } from "@/utils/format";
import { CHART_COLORS } from "@/utils/game";
import { downloadBlob } from "@/utils/download";

export function TournamentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const tournament = useTournament(id);
  const isCompleted = tournament.data?.status === "COMPLETED";
  const results = useTournamentResults(id, isCompleted);
  const statistics = useStatistics("tournament", id, isCompleted);

  const [selectedStrategy, setSelectedStrategy] = useState<TournamentRanking | null>(null);
  const runAction = useApiAction(tournamentApi.run);
  const exportAction = useApiAction(tournamentApi.exportResultsCsv);

  const run = async () => {
    if (!id) return;
    const outcome = await runAction.execute(id);
    if (outcome) {
      toast.success("Tournament complete", `${outcome.matches_played} matches simulated.`);
      await tournament.refresh();
      await results.refresh();
      await statistics.refresh();
    } else if (runAction.error) {
      toast.apiError(runAction.error, "Could not run the tournament");
    }
  };

  const exportCsv = async () => {
    if (!id) return;
    const blob = await exportAction.execute(id);
    if (blob) {
      downloadBlob(blob, `tournament-${id}-results.csv`);
      toast.success("Download started", "Ranking table exported as CSV.");
    } else if (exportAction.error) {
      toast.apiError(exportAction.error, "Export failed");
    }
  };

  if (tournament.loading) {
    return (
      <>
        <PageHeader title="Tournament" icon={<Trophy className="h-5 w-5" />} />
        <SkeletonStats count={4} />
      </>
    );
  }

  if (tournament.error) {
    return (
      <>
        <PageHeader title="Tournament" icon={<Trophy className="h-5 w-5" />} />
        <Card>
          <ErrorState error={tournament.error} onRetry={tournament.refresh} />
        </Card>
      </>
    );
  }

  if (!tournament.data) return null;

  const detail = tournament.data;
  const rankings = results.data?.rankings ?? [];

  const columns: Column<TournamentRanking>[] = [
    {
      key: "rank",
      header: "Rank",
      render: (row) => (
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-lab-100 font-mono text-xs font-semibold text-lab-800">
          {row.rank}
        </span>
      ),
    },
    {
      key: "strategy",
      header: "Strategy",
      render: (row) => (
        <div>
          <p className="font-medium text-lab-900">{row.strategy_name}</p>
          <p className="font-mono text-[11px] text-lab-500">{row.strategy_id}</p>
        </div>
      ),
    },
    {
      key: "total",
      header: "Total score",
      align: "right",
      render: (row) => (
        <span className="font-mono font-semibold tabular-nums">{formatScore(row.total_score)}</span>
      ),
    },
    {
      key: "average",
      header: "Average",
      align: "right",
      render: (row) => <span className="font-mono tabular-nums">{formatNumber(row.average_score)}</span>,
    },
    {
      key: "matches",
      header: "Matches",
      align: "right",
      hideOnMobile: true,
      render: (row) => <span className="font-mono tabular-nums">{row.matches_played}</span>,
    },
    {
      key: "record",
      header: "W / D / L",
      align: "center",
      hideOnMobile: true,
      render: (row) => (
        <span className="font-mono text-xs tabular-nums">
          {row.wins} / {row.draws} / {row.losses}
        </span>
      ),
    },
    {
      key: "cooperation",
      header: "Cooperation",
      align: "right",
      render: (row) => (
        <span className="font-mono tabular-nums text-emerald-300">
          {formatPercent(row.cooperation_rate)}
        </span>
      ),
    },
    {
      key: "defection",
      header: "Defection",
      align: "right",
      hideOnMobile: true,
      render: (row) => (
        <span className="font-mono tabular-nums text-rose-300">
          {formatPercent(row.defection_rate)}
        </span>
      ),
    },
  ];

  const scoreData = rankings.map((row) => ({ label: row.strategy_id, value: row.total_score }));
  const averageData = rankings.map((row) => ({ label: row.strategy_id, value: row.average_score }));
  const ratesData = rankings.map((row) => ({
    label: row.strategy_id,
    Cooperation: row.cooperation_rate,
    Defection: row.defection_rate,
  }));
  const cooperationOverTime = (statistics.data?.cooperation_by_round ?? []).map((point) => ({
    round: point.round_number,
    rate: point.cooperation_rate,
  }));

  return (
    <>
      <PageHeader
        title={detail.name}
        description={detail.description ?? undefined}
        icon={<Trophy className="h-5 w-5" />}
        breadcrumbs={[
          { label: "Tournaments", to: "/tournament" },
          { label: detail.name },
        ]}
        actions={
          <>
            <StatusBadge status={detail.status} />
            {isCompleted ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<ListOrdered className="h-4 w-4" />}
                  onClick={() => navigate(`/tournament/${detail.id}/matches`)}
                >
                  All matches
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Download className="h-4 w-4" />}
                  loading={exportAction.pending}
                  onClick={exportCsv}
                >
                  Export CSV
                </Button>
              </>
            ) : null}
            {detail.status === "PENDING" || detail.status === "FAILED" ? (
              <RequireRole roles={["ADMIN", "TEACHER"]} fallback={null}>
                <Button
                  size="sm"
                  icon={<Play className="h-4 w-4" />}
                  loading={runAction.pending}
                  onClick={run}
                >
                  Run tournament
                </Button>
              </RequireRole>
            ) : null}
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Strategies" value={detail.strategy_codes.length} />
        <StatCard label="Rounds per match" value={detail.rounds_per_match} />
        <StatCard label="Matches played" value={detail.matches_played} />
        <StatCard
          label="Random seed"
          value={detail.seed ?? "None"}
          hint="With a seed, re-creating the same configuration reproduces these results exactly."
        />
      </div>

      {detail.status === "FAILED" && detail.error_message ? (
        <Card className="mt-4 border-rose-500/30">
          <CardBody>
            <p className="text-sm font-medium text-rose-300">The run failed</p>
            <p className="mt-1 font-mono text-xs text-rose-300">{detail.error_message}</p>
          </CardBody>
        </Card>
      ) : null}

      {detail.status === "PENDING" ? (
        <Card className="mt-4">
          <EmptyState
            icon={<Play className="h-6 w-6" />}
            title="Not run yet"
            description="This tournament is configured but has not been simulated. Run it to produce the ranking table."
          />
        </Card>
      ) : null}

      {isCompleted ? (
        <>
          {results.loading ? <SkeletonTable rows={6} columns={6} /> : null}
          {results.error ? (
            <Card className="mt-4">
              <ErrorState error={results.error} onRetry={results.refresh} />
            </Card>
          ) : null}

          {rankings.length > 0 ? (
            <>
              <Card className="mt-4">
                <CardHeader
                  title="Final ranking"
                  description="Click a strategy for its full record"
                  actions={
                    results.data?.winner_strategy_id ? (
                      <Badge tone="accent" icon={<Trophy className="h-3 w-3" aria-hidden />}>
                        Winner: {results.data.winner_strategy_id}
                      </Badge>
                    ) : null
                  }
                />
                <DataTable
                  columns={columns}
                  rows={rankings}
                  rowKey={(row) => row.strategy_id}
                  caption="Tournament ranking"
                  onRowClick={setSelectedStrategy}
                  highlightRow={(row) => row.rank === 1}
                />
                <div className="border-t border-lab-250 px-5 py-3">
                  <p className="text-xs text-lab-600">{results.data?.note}</p>
                </div>
              </Card>

              <div className="mt-4 grid gap-4 xl:grid-cols-2">
                <ChartFrame
                  title="Total score by strategy"
                  description="Points accumulated across the whole round robin"
                >
                  <CategoryBarChart
                    data={scoreData}
                    xLabel="Strategy"
                    yLabel="Total score"
                    color={CHART_COLORS.neutral}
                  />
                </ChartFrame>

                <ChartFrame
                  title="Average payoff per round"
                  description="Total score divided by rounds played"
                >
                  <CategoryBarChart
                    data={averageData}
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
                    data={ratesData}
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

                {cooperationOverTime.length > 0 ? (
                  <ChartFrame
                    title="Cooperation across the match length"
                    description="All strategies pooled, by round number"
                    hint="Shows whether cooperation held up or decayed as matches progressed."
                  >
                    <MultiLineChart
                      data={cooperationOverTime}
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

              <Card className="mt-4">
                <CardHeader
                  title="Head-to-head"
                  description="Average payoff per round for each strategy against each opponent"
                />
                <CardBody>
                  {statistics.data ? (
                    <HeadToHeadTable
                      entries={statistics.data.head_to_head}
                      strategies={rankings.map((row) => row.strategy_id)}
                    />
                  ) : (
                    <p className="text-sm text-lab-600">Loading head-to-head data…</p>
                  )}
                </CardBody>
              </Card>
            </>
          ) : null}
        </>
      ) : null}

      <Dialog
        open={selectedStrategy !== null}
        onClose={() => setSelectedStrategy(null)}
        title={selectedStrategy?.strategy_name ?? ""}
        description={`Rank ${selectedStrategy?.rank} in this tournament`}
      >
        {selectedStrategy ? (
          <dl className="grid grid-cols-2 gap-3">
            {[
              ["Total score", formatScore(selectedStrategy.total_score)],
              ["Average per round", formatNumber(selectedStrategy.average_score)],
              ["Matches played", String(selectedStrategy.matches_played)],
              ["Rounds played", String(selectedStrategy.rounds_played)],
              ["Wins", String(selectedStrategy.wins)],
              ["Draws", String(selectedStrategy.draws)],
              ["Losses", String(selectedStrategy.losses)],
              ["Cooperation rate", formatPercent(selectedStrategy.cooperation_rate)],
              ["Defection rate", formatPercent(selectedStrategy.defection_rate)],
              ["Cooperations", String(selectedStrategy.cooperation_count)],
              ["Defections", String(selectedStrategy.defection_count)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-lab-250 p-2.5">
                <dt className="text-[11px] tracking-wide text-lab-600 uppercase">{label}</dt>
                <dd className="font-mono text-sm font-semibold text-lab-900">{value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
      </Dialog>

      {isCompleted ? (
        <p className="mt-4 text-center text-xs text-lab-600">
          <Link to={`/tournament/${detail.id}/matches`} className="text-violet-400 hover:underline">
            Inspect every individual match
          </Link>
        </p>
      ) : null}
    </>
  );
}

function HeadToHeadTable({
  entries,
  strategies,
}: {
  entries: Array<{ strategy_id: string; opponent_id: string; average_payoff: number }>;
  strategies: string[];
}) {
  const lookup = new Map(entries.map((entry) => [`${entry.strategy_id}|${entry.opponent_id}`, entry.average_payoff]));

  return (
    <div className="table-scroll">
      <table className="w-full min-w-[32rem] border-collapse text-sm">
        <caption className="sr-only">
          Average payoff per round, row strategy against column opponent
        </caption>
        <thead>
          <tr>
            <th scope="col" className="px-2 py-2 text-xs text-lab-600">
              vs →
            </th>
            {strategies.map((code) => (
              <th key={code} scope="col" className="px-2 py-2 text-xs font-medium text-lab-700">
                {code}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {strategies.map((rowCode) => (
            <tr key={rowCode} className="border-t border-lab-250">
              <th scope="row" className="px-2 py-2 text-xs font-medium text-lab-700">
                {rowCode}
              </th>
              {strategies.map((columnCode) => {
                const value = lookup.get(`${rowCode}|${columnCode}`);
                return (
                  <td
                    key={columnCode}
                    className="px-2 py-2 text-center font-mono text-xs tabular-nums"
                  >
                    {value === undefined ? (
                      <span className="text-lab-400">—</span>
                    ) : (
                      value.toFixed(2)
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
