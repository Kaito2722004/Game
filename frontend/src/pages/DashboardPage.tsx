import { useMemo } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Handshake,
  LayoutDashboard,
  Swords,
  Trophy,
  Users,
} from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { SkeletonStats } from "@/components/common/Skeleton";
import { StatCard } from "@/components/common/StatCard";
import { ChartFrame } from "@/components/charts/ChartFrame";
import { CategoryBarChart, GroupedBarChart } from "@/components/charts/Charts";
import { ConceptCard } from "@/components/game/ConceptCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { useExperiments, useTournaments, useTournamentResults } from "@/hooks";
import { formatDate, formatPercent, formatScore } from "@/utils/format";
import { CHART_COLORS } from "@/utils/game";
import { StatusBadge } from "@/features/tournament/StatusBadge";

/**
 * Overview of everything run so far.
 *
 * The charts show the most recent completed tournament, because that is the
 * only run whose numbers are directly comparable.
 */
export function DashboardPage() {
  const tournaments = useTournaments();
  const experiments = useExperiments();

  const latestCompleted = useMemo(
    () => tournaments.data?.find((item) => item.status === "COMPLETED") ?? null,
    [tournaments.data],
  );

  const results = useTournamentResults(latestCompleted?.id, Boolean(latestCompleted));

  const totals = useMemo(() => {
    const tournamentList = tournaments.data ?? [];
    const experimentList = experiments.data ?? [];
    return {
      tournaments: tournamentList.length,
      experiments: experimentList.length,
      participants: experimentList.reduce((sum, item) => sum + item.participant_count, 0),
      matches: tournamentList.reduce((sum, item) => sum + item.matches_played, 0),
    };
  }, [tournaments.data, experiments.data]);

  /** Pooled cooperation across the latest completed tournament. */
  const cooperation = useMemo(() => {
    const rankings = results.data?.rankings ?? [];
    if (rankings.length === 0) return null;
    const cooperations = rankings.reduce((sum, row) => sum + row.cooperation_count, 0);
    const defections = rankings.reduce((sum, row) => sum + row.defection_count, 0);
    const total = cooperations + defections;
    if (total === 0) return null;
    return { rate: cooperations / total, defectionRate: defections / total };
  }, [results.data]);

  const rankingData = (results.data?.rankings ?? []).map((row) => ({
    label: row.strategy_id,
    value: row.total_score,
  }));

  const cooperationData = (results.data?.rankings ?? []).map((row) => ({
    label: row.strategy_id,
    Cooperation: row.cooperation_rate,
    Defection: row.defection_rate,
  }));

  const averageData = (results.data?.rankings ?? []).map((row) => ({
    label: row.strategy_id,
    value: row.average_score,
  }));

  const loading = tournaments.loading || experiments.loading;

  if (tournaments.error) {
    return (
      <>
        <PageHeader title="Dashboard" icon={<LayoutDashboard className="h-5 w-5" />} />
        <Card>
          <ErrorState error={tournaments.error} onRetry={tournaments.refresh} />
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Every tournament and classroom experiment recorded by the backend."
        icon={<LayoutDashboard className="h-5 w-5" />}
      />

      {loading ? (
        <SkeletonStats count={4} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Tournaments"
            value={totals.tournaments}
            icon={<Trophy className="h-4 w-4" />}
            hint="Round-robin simulations created in this system."
          />
          <StatCard
            label="Experiments"
            value={totals.experiments}
            icon={<Users className="h-4 w-4" />}
            hint="Classroom sessions with human participants."
          />
          <StatCard
            label="Participants"
            value={totals.participants}
            icon={<Users className="h-4 w-4" />}
            hint="People registered across all experiments."
          />
          <StatCard
            label="Simulated matches"
            value={formatScore(totals.matches)}
            icon={<Swords className="h-4 w-4" />}
            hint="Total matches played across every tournament run."
          />
        </div>
      )}

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <StatCard
          label="Cooperation rate"
          value={cooperation ? formatPercent(cooperation.rate) : "—"}
          tone="cooperate"
          icon={<Handshake className="h-4 w-4" />}
          loading={results.loading}
          hint="Share of all moves that were Cooperate, in the most recent completed tournament."
          footer={latestCompleted ? `From "${latestCompleted.name}"` : "No completed tournament yet"}
        />
        <StatCard
          label="Defection rate"
          value={cooperation ? formatPercent(cooperation.defectionRate) : "—"}
          tone="defect"
          icon={<Swords className="h-4 w-4" />}
          loading={results.loading}
          hint="Share of all moves that were Defect, in the most recent completed tournament."
          footer={latestCompleted ? `From "${latestCompleted.name}"` : "Run a tournament to populate this"}
        />
      </div>

      {latestCompleted && rankingData.length > 0 ? (
        <div className="mt-6 grid gap-4 xl:grid-cols-2">
          <ChartFrame
            title="Strategy ranking"
            description={`Total score in "${latestCompleted.name}"`}
            hint="Total points each strategy earned across every match of the round robin."
          >
            <CategoryBarChart
              data={rankingData}
              xLabel="Strategy"
              yLabel="Total score"
              color={CHART_COLORS.neutral}
            />
          </ChartFrame>

          <ChartFrame
            title="Cooperation versus defection"
            description="Share of each strategy's moves"
            hint="How often each strategy chose Cooperate rather than Defect."
          >
            <GroupedBarChart
              data={cooperationData}
              xKey="label"
              xLabel="Strategy"
              yLabel="Share of moves"
              stacked
              domain={[0, 1]}
              formatter={(value) => formatPercent(value, 0)}
              series={[
                { key: "Cooperation", name: "Cooperate", color: CHART_COLORS.cooperate },
                { key: "Defection", name: "Defect", color: CHART_COLORS.defect },
              ]}
            />
          </ChartFrame>

          <ChartFrame
            title="Average payoff per round"
            description="Points earned per round played"
            hint="Total score divided by rounds played. Mutual cooperation pays 3 per round in the classic matrix, mutual defection 1."
          >
            <CategoryBarChart
              data={averageData}
              xLabel="Strategy"
              yLabel="Average payoff"
              color={CHART_COLORS.accent}
              formatter={(value) => value.toFixed(2)}
            />
          </ChartFrame>

          <Card>
            <CardHeader
              title="How the Prisoner's Dilemma works"
              description="The idea behind every number on this page"
            />
            <CardBody className="space-y-3">
              <p className="text-sm leading-relaxed text-slate-700">
                Two players choose privately and at the same time: cooperate or defect.
                If both cooperate they each do well. If one defects while the other
                cooperates, the defector does best of all and the cooperator does worst.
                If both defect, they each do badly.
              </p>
              <p className="text-sm leading-relaxed text-slate-700">
                Defecting pays more whatever the other player does, so it is the rational
                individual choice — yet if both follow that reasoning they end up worse
                off than if both had cooperated. That gap between individual and
                collective rationality is the dilemma.
              </p>
              <ConceptCard {...{ term: "Repeated game", definition: "The game is played multiple times, so current actions can affect future interactions." }} />
              <Link
                to="/game-theory"
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
              >
                Read the full explanation
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </CardBody>
          </Card>
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader
            title="Recent tournaments"
            actions={
              <Link
                to="/tournament"
                className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
              >
                View all
              </Link>
            }
          />
          {(tournaments.data ?? []).length === 0 ? (
            <EmptyState
              icon={<Trophy className="h-6 w-6" />}
              title="No tournaments yet"
              description="Create a round robin to compare the six strategies."
            />
          ) : (
            <ul className="divide-y divide-lab-100">
              {(tournaments.data ?? []).slice(0, 5).map((tournament) => (
                <li key={tournament.id}>
                  <Link
                    to={`/tournament/${tournament.id}`}
                    className="flex items-center justify-between gap-3 px-5 py-3 transition-colors hover:bg-lab-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-lab-900">
                        {tournament.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {tournament.strategy_codes.length} strategies ·{" "}
                        {tournament.rounds_per_match} rounds · {formatDate(tournament.created_at)}
                      </p>
                    </div>
                    <StatusBadge status={tournament.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardHeader
            title="Recent experiments"
            actions={
              <Link
                to="/experiments"
                className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
              >
                View all
              </Link>
            }
          />
          {(experiments.data ?? []).length === 0 ? (
            <EmptyState
              icon={<Users className="h-6 w-6" />}
              title="No experiments yet"
              description="Set up a classroom session to record how people actually play."
            />
          ) : (
            <ul className="divide-y divide-lab-100">
              {(experiments.data ?? []).slice(0, 5).map((experiment) => (
                <li key={experiment.id}>
                  <Link
                    to={`/experiments/${experiment.id}`}
                    className="flex items-center justify-between gap-3 px-5 py-3 transition-colors hover:bg-lab-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-lab-900">
                        {experiment.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {experiment.participant_count} participants · {experiment.rounds} rounds
                      </p>
                    </div>
                    <Badge
                      tone={
                        experiment.status === "COMPLETED"
                          ? "success"
                          : experiment.status === "RUNNING"
                            ? "info"
                            : "neutral"
                      }
                    >
                      {experiment.status}
                    </Badge>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  );
}
