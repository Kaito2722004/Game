import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Database,
  Download,
  FlaskConical,
  History,
  Trophy,
  Users,
} from "lucide-react";
import { historyApi } from "@/api/historyApi";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { DataTable, type Column } from "@/components/common/DataTable";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { SkeletonStats, SkeletonTable } from "@/components/common/Skeleton";
import { StatCard } from "@/components/common/StatCard";
import { Tabs, type TabItem } from "@/components/common/Tabs";
import { PageHeader } from "@/components/layout/PageHeader";
import { useApiResource } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import type { HistoryEntry, HistoryKind } from "@/types";
import { downloadBlob } from "@/utils/download";
import { formatDate, formatPercent, formatScore } from "@/utils/format";

const TABS: TabItem[] = [
  { id: "ALL", label: "Everything", icon: <Database className="h-4 w-4" aria-hidden /> },
  { id: "TOURNAMENT", label: "Tournaments", icon: <Trophy className="h-4 w-4" aria-hidden /> },
  { id: "EXPERIMENT", label: "Experiments", icon: <Users className="h-4 w-4" aria-hidden /> },
  {
    id: "SIMULATED_MATCH",
    label: "Simulated matches",
    icon: <FlaskConical className="h-4 w-4" aria-hidden />,
  },
];

const KIND_META: Record<
  HistoryKind,
  { label: string; tone: "accent" | "info" | "neutral"; icon: typeof Trophy }
> = {
  TOURNAMENT: { label: "Tournament", tone: "accent", icon: Trophy },
  EXPERIMENT: { label: "Experiment", tone: "info", icon: Users },
  SIMULATED_MATCH: { label: "Simulated", tone: "neutral", icon: FlaskConical },
};

/** Where clicking a row takes you, per kind. */
function detailPath(entry: HistoryEntry): string | null {
  switch (entry.kind) {
    case "TOURNAMENT":
      return `/tournament/${entry.id}`;
    case "EXPERIMENT":
      return `/experiments/${entry.id}`;
    default:
      // Persisted one-off matches have no page of their own.
      return null;
  }
}

/**
 * Everything that has been played, in one place.
 *
 * The backend flattens tournaments, classroom experiments and kept one-off
 * simulations into a single ordered list, so this page only has to present
 * it. Totals always describe the whole record, even while a tab narrows the
 * table below.
 */
export function HistoryPage() {
  const [tab, setTab] = useState<string>("ALL");
  const navigate = useNavigate();
  const toast = useToast();

  const kind = tab === "ALL" ? undefined : (tab as HistoryKind);
  const history = useApiResource(() => historyApi.list(kind), [kind]);

  const totals = history.data?.totals;
  const entries = useMemo(() => history.data?.entries ?? [], [history.data]);

  /** Export the visible rows. Assembling a CSV from data already on screen. */
  const exportCsv = () => {
    if (entries.length === 0) return;
    const header = [
      "kind",
      "title",
      "status",
      "occurred_at",
      "matches",
      "rounds",
      "cooperation_rate",
      "headline",
    ];
    const escape = (value: unknown) => {
      const text = value === null || value === undefined ? "" : String(value);
      return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    };
    const body = entries.map((entry) =>
      [
        entry.kind,
        entry.title,
        entry.status,
        entry.occurred_at,
        entry.matches,
        entry.rounds,
        entry.cooperation_rate ?? "",
        entry.headline ?? "",
      ]
        .map(escape)
        .join(","),
    );
    const csv = [header.join(","), ...body].join("\n");
    downloadBlob(new Blob([csv], { type: "text/csv;charset=utf-8" }), "game-history.csv");
    toast.success("Download started", `${entries.length} rows exported.`);
  };

  const columns: Column<HistoryEntry>[] = [
    {
      key: "kind",
      header: "Type",
      render: (row) => {
        const meta = KIND_META[row.kind];
        return (
          <Badge tone={meta.tone} icon={<meta.icon className="h-3 w-3" aria-hidden />}>
            {meta.label}
          </Badge>
        );
      },
    },
    {
      key: "title",
      header: "What was played",
      render: (row) => (
        <div className="min-w-0">
          <p className="font-medium text-lab-900">{row.title}</p>
          {row.subtitle ? <p className="text-xs text-lab-600">{row.subtitle}</p> : null}
        </div>
      ),
    },
    {
      key: "when",
      header: "When",
      hideOnMobile: true,
      render: (row) => <span className="text-xs text-lab-600">{formatDate(row.occurred_at)}</span>,
    },
    {
      key: "rounds",
      header: "Rounds",
      align: "right",
      render: (row) => (
        <span className="font-mono text-sm tabular-nums">{formatScore(row.rounds)}</span>
      ),
    },
    {
      key: "cooperation",
      header: "Cooperation",
      align: "right",
      render: (row) =>
        row.cooperation_rate === null ? (
          <span className="text-lab-500">—</span>
        ) : (
          <span className="font-mono text-sm tabular-nums text-emerald-300">
            {formatPercent(row.cooperation_rate)}
          </span>
        ),
    },
    {
      key: "result",
      header: "Result",
      hideOnMobile: true,
      render: (row) => (
        <span className="text-xs text-lab-700">{row.headline ?? row.status}</span>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Game History"
        description="Every tournament, classroom session and saved simulation recorded by the backend, newest first."
        icon={<History className="h-5 w-5" />}
        actions={
          <Button
            variant="secondary"
            size="sm"
            icon={<Download className="h-4 w-4" />}
            onClick={exportCsv}
            disabled={entries.length === 0}
          >
            Export CSV
          </Button>
        }
      />

      {history.loading && !history.data ? <SkeletonStats count={4} /> : null}

      {history.error ? (
        <Card>
          <ErrorState error={history.error} onRetry={history.refresh} />
        </Card>
      ) : null}

      {totals ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Rounds played"
              value={formatScore(totals.total_rounds_played)}
              icon={<Database className="h-4 w-4" />}
              hint="Every recorded round: tournament matches, saved simulations and human play combined."
            />
            <StatCard
              label="Tournaments"
              value={totals.tournaments}
              icon={<Trophy className="h-4 w-4" />}
              footer={`${formatScore(totals.tournament_matches)} matches`}
            />
            <StatCard
              label="Experiments"
              value={totals.experiments}
              icon={<Users className="h-4 w-4" />}
              footer={`${totals.human_pairs} pairs · ${totals.human_rounds} rounds`}
            />
            <StatCard
              label="Saved simulations"
              value={totals.simulated_matches}
              icon={<FlaskConical className="h-4 w-4" />}
              footer={`${totals.survey_responses} survey responses`}
            />
          </div>

          <Tabs items={TABS} active={tab} onChange={setTab} className="mt-6 mb-4" />

          <Card>
            <CardHeader
              title={TABS.find((item) => item.id === tab)?.label ?? "Everything"}
              description={
                tab === "SIMULATED_MATCH"
                  ? "One-off matches run in the simulator with 'Store this match' enabled."
                  : "Select a row to open its full record."
              }
              actions={<Badge tone="neutral">{entries.length} shown</Badge>}
            />

            {history.loading ? (
              <SkeletonTable rows={5} columns={5} />
            ) : entries.length === 0 ? (
              <EmptyState
                icon={<History className="h-6 w-6" />}
                title="Nothing recorded yet"
                description={
                  tab === "SIMULATED_MATCH"
                    ? "Run a match in the simulator with persistence enabled and it will be listed here."
                    : "Run a tournament or a classroom experiment and it will appear here."
                }
              />
            ) : (
              <DataTable
                columns={columns}
                rows={entries}
                rowKey={(row) => `${row.kind}-${row.id}`}
                caption="Everything that has been played"
                onRowClick={(row) => {
                  const path = detailPath(row);
                  if (path) navigate(path);
                }}
              />
            )}
          </Card>

          <Card className="mt-4">
            <CardBody>
              <p className="text-xs leading-relaxed text-lab-600">
                Rounds, scores and cooperation rates are read from the stored records
                rather than recomputed, so these figures match exactly what each
                tournament and session saved. Saved simulations are individual matches
                and have no page of their own; open the simulator to run new ones.
              </p>
            </CardBody>
          </Card>
        </>
      ) : null}
    </>
  );
}
