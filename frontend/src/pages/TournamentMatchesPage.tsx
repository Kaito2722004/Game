import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { ListOrdered, Swords } from "lucide-react";
import { tournamentApi } from "@/api/tournamentApi";
import { Badge } from "@/components/common/Badge";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { DataTable, type Column } from "@/components/common/DataTable";
import { Dialog } from "@/components/common/Dialog";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { SelectField } from "@/components/common/Field";
import { SkeletonTable } from "@/components/common/Skeleton";
import { StatCard } from "@/components/common/StatCard";
import { ChartFrame } from "@/components/charts/ChartFrame";
import { MultiLineChart } from "@/components/charts/Charts";
import { RoundHistoryTable } from "@/components/game/RoundHistoryTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { useApiAction, useTournament, useTournamentMatches } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import type { TournamentMatch, TournamentMatchDetail } from "@/types";
import { formatNumber, formatPercent, humanizeCode } from "@/utils/format";
import { CHART_COLORS, OUTCOME_LABELS, OUTCOME_ORDER } from "@/utils/game";

/** Every match of a tournament, with a drill-down into the round history. */
export function TournamentMatchesPage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();

  const tournament = useTournament(id);
  const matches = useTournamentMatches(id);

  const [filter, setFilter] = useState("");
  const [detail, setDetail] = useState<TournamentMatchDetail | null>(null);
  const loadDetail = useApiAction(tournamentApi.matchDetail);

  const openMatch = async (match: TournamentMatch) => {
    if (!id) return;
    const result = await loadDetail.execute(id, match.id);
    if (result) setDetail(result);
    else if (loadDetail.error) toast.apiError(loadDetail.error, "Could not load the match");
  };

  const strategyCodes = tournament.data?.strategy_codes ?? [];

  const filtered = useMemo(() => {
    const rows = matches.data ?? [];
    if (!filter) return rows;
    return rows.filter(
      (row) => row.strategy_a_id === filter || row.strategy_b_id === filter,
    );
  }, [matches.data, filter]);

  const columns: Column<TournamentMatch>[] = [
    {
      key: "sequence",
      header: "#",
      render: (row) => <span className="font-mono text-xs text-lab-600">{row.sequence}</span>,
    },
    {
      key: "pairing",
      header: "Pairing",
      render: (row) => (
        <span className="text-sm font-medium text-lab-900">
          {humanizeCode(row.strategy_a_id)}{" "}
          <span className="text-lab-500">vs</span> {humanizeCode(row.strategy_b_id)}
        </span>
      ),
    },
    {
      key: "score",
      header: "Score",
      align: "center",
      render: (row) => (
        <span className="font-mono text-sm tabular-nums">
          {formatNumber(row.player_a_score, 0)} – {formatNumber(row.player_b_score, 0)}
        </span>
      ),
    },
    {
      key: "rounds",
      header: "Rounds",
      align: "right",
      hideOnMobile: true,
      render: (row) => <span className="font-mono text-sm">{row.rounds_played}</span>,
    },
    {
      key: "coopA",
      header: "A cooperation",
      align: "right",
      hideOnMobile: true,
      render: (row) => (
        <span className="font-mono text-xs text-emerald-300">
          {formatPercent(row.player_a_cooperation_count / Math.max(1, row.rounds_played))}
        </span>
      ),
    },
    {
      key: "winner",
      header: "Winner",
      render: (row) =>
        row.winner ? (
          <Badge tone="accent">{humanizeCode(row.winner)}</Badge>
        ) : (
          <Badge tone="neutral">Draw</Badge>
        ),
    },
  ];

  const detailCumulative = useMemo(() => {
    if (!detail) return [];
    let a = 0;
    let b = 0;
    return detail.rounds.map((round) => {
      a += round.player_a_payoff;
      b += round.player_b_payoff;
      return { round: round.round_number, a, b };
    });
  }, [detail]);

  const detailOutcomes = useMemo(() => {
    if (!detail) return null;
    const counts: Record<string, number> = { CC: 0, CD: 0, DC: 0, DD: 0 };
    for (const round of detail.rounds) counts[round.outcome] += 1;
    return counts;
  }, [detail]);

  return (
    <>
      <PageHeader
        title="Tournament matches"
        description="Every pairing simulated in this tournament. Open one to see it round by round."
        icon={<ListOrdered className="h-5 w-5" />}
        breadcrumbs={[
          { label: "Tournaments", to: "/tournament" },
          { label: tournament.data?.name ?? "Tournament", to: `/tournament/${id}` },
          { label: "Matches" },
        ]}
      />

      <Card>
        <CardHeader
          title="All matches"
          description={`${filtered.length} shown`}
          actions={
            strategyCodes.length > 0 ? (
              <div className="w-56">
                <SelectField
                  label="Filter by strategy"
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                >
                  <option value="">All strategies</option>
                  {strategyCodes.map((code) => (
                    <option key={code} value={code}>
                      {humanizeCode(code)}
                    </option>
                  ))}
                </SelectField>
              </div>
            ) : null
          }
        />

        {matches.loading ? <SkeletonTable rows={6} columns={5} /> : null}
        {matches.error ? <ErrorState error={matches.error} onRetry={matches.refresh} /> : null}
        {matches.data && matches.data.length === 0 ? (
          <EmptyState
            icon={<Swords className="h-6 w-6" />}
            title="No matches recorded"
            description="This tournament has not been run yet."
          />
        ) : null}
        {filtered.length > 0 ? (
          <DataTable
            columns={columns}
            rows={filtered}
            rowKey={(row) => row.id}
            caption="Tournament matches"
            onRowClick={openMatch}
          />
        ) : null}
      </Card>

      <Dialog
        open={detail !== null}
        onClose={() => setDetail(null)}
        title={
          detail
            ? `${humanizeCode(detail.strategy_a_id)} vs ${humanizeCode(detail.strategy_b_id)}`
            : ""
        }
        description={detail ? `Match ${detail.sequence} · ${detail.rounds_played} rounds` : undefined}
        maxWidth="max-w-4xl"
      >
        {detail ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <StatCard
                label={humanizeCode(detail.strategy_a_id)}
                value={formatNumber(detail.player_a_score, 0)}
                footer={`Cooperated ${detail.player_a_cooperation_count} times`}
              />
              <StatCard
                label={humanizeCode(detail.strategy_b_id)}
                value={formatNumber(detail.player_b_score, 0)}
                footer={`Cooperated ${detail.player_b_cooperation_count} times`}
              />
              <StatCard
                label="Result"
                value={detail.winner ? humanizeCode(detail.winner) : "Draw"}
              />
            </div>

            {detailOutcomes ? (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {OUTCOME_ORDER.map((outcome) => (
                  <div key={outcome} className="rounded-lg border border-lab-250 p-2.5 text-center">
                    <p className="font-mono text-xs text-lab-600">{outcome}</p>
                    <p className="text-lg font-semibold text-lab-900">
                      {detailOutcomes[outcome]}
                    </p>
                    <p className="text-[10px] leading-tight text-lab-600">
                      {OUTCOME_LABELS[outcome]}
                    </p>
                  </div>
                ))}
              </div>
            ) : null}

            <ChartFrame title="Cumulative payoff" description="Running totals through the match" height={220}>
              <MultiLineChart
                data={detailCumulative}
                xKey="round"
                xLabel="Round"
                yLabel="Cumulative payoff"
                series={[
                  {
                    key: "a",
                    name: humanizeCode(detail.strategy_a_id),
                    color: CHART_COLORS.playerA,
                  },
                  {
                    key: "b",
                    name: humanizeCode(detail.strategy_b_id),
                    color: CHART_COLORS.playerB,
                  },
                ]}
              />
            </ChartFrame>

            <Card>
              <CardBody className="p-0">
                <RoundHistoryTable
                  rounds={detail.rounds}
                  labelA={humanizeCode(detail.strategy_a_id)}
                  labelB={humanizeCode(detail.strategy_b_id)}
                  initialLimit={15}
                />
              </CardBody>
            </Card>
          </div>
        ) : null}
      </Dialog>
    </>
  );
}
