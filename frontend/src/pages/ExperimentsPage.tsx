import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Users } from "lucide-react";
import { experimentApi } from "@/api/experimentApi";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { DataTable, type Column } from "@/components/common/DataTable";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { CheckboxField, SelectField, TextField } from "@/components/common/Field";
import { SkeletonTable } from "@/components/common/Skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { useApiAction, useExperiments, usePayoffMatrices } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import { RequireRole } from "@/features/auth/RequireRole";
import { ExperimentStatusBadge } from "@/features/tournament/StatusBadge";
import type { Experiment } from "@/types";
import { formatDate } from "@/utils/format";

/** Create and browse classroom experiments. */
export function ExperimentsPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const experiments = useExperiments();
  const matrices = usePayoffMatrices();

  const [name, setName] = useState("Game Theory Classroom Experiment");
  const [description, setDescription] = useState("");
  const [rounds, setRounds] = useState(10);
  const [anonymous, setAnonymous] = useState(true);
  const [survey, setSurvey] = useState(true);
  const [matrixId, setMatrixId] = useState("");

  const create = useApiAction(experimentApi.create);

  const submit = async () => {
    const created = await create.execute({
      name: name.trim(),
      description: description.trim() || null,
      rounds,
      anonymous_mode: anonymous,
      trust_survey_enabled: survey,
      payoff_matrix_id: matrixId || null,
    });

    if (created) {
      toast.success("Experiment created", "Add participants next, then start the session.");
      void experiments.refresh();
      navigate(`/experiments/${created.id}`);
    } else if (create.error) {
      toast.apiError(create.error, "Could not create the experiment");
    }
  };

  const columns: Column<Experiment>[] = [
    {
      key: "name",
      header: "Experiment",
      render: (row) => (
        <div className="min-w-0">
          <Link
            to={`/experiments/${row.id}`}
            className="font-medium text-indigo-700 hover:text-indigo-900"
          >
            {row.name}
          </Link>
          <p className="text-xs text-slate-500">
            {row.rounds} rounds · {row.anonymous_mode ? "anonymous" : "named"}
          </p>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <ExperimentStatusBadge status={row.status} />,
    },
    {
      key: "participants",
      header: "Participants",
      align: "right",
      render: (row) => <span className="font-mono text-sm">{row.participant_count}</span>,
    },
    {
      key: "pairs",
      header: "Pairs",
      align: "right",
      hideOnMobile: true,
      render: (row) => <span className="font-mono text-sm">{row.pair_count}</span>,
    },
    {
      key: "created",
      header: "Created",
      hideOnMobile: true,
      render: (row) => <span className="text-xs text-slate-500">{formatDate(row.created_at)}</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="Human Experiment"
        description="Run the Prisoner's Dilemma with real participants and compare what they do with the theoretical prediction."
        icon={<Users className="h-5 w-5" />}
      />

      <div className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader
            title="New experiment"
            description="Settings can still be changed while it is a draft."
          />
          <CardBody>
            <RequireRole roles={["ADMIN", "TEACHER"]}>
              <div className="space-y-4">
                <TextField
                  label="Name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />
                <TextField
                  label="Description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Optional"
                />
                <TextField
                  label="Rounds per pair"
                  type="number"
                  min={1}
                  max={500}
                  value={rounds}
                  onChange={(event) => setRounds(Number(event.target.value))}
                  help="Ten rounds works well for a single class period."
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

                <CheckboxField
                  label="Anonymous mode"
                  description="Report participants by code instead of by name."
                  checked={anonymous}
                  onChange={(event) => setAnonymous(event.target.checked)}
                />
                <CheckboxField
                  label="Enable trust survey"
                  description="Ask about expected cooperation before play and trust afterwards."
                  checked={survey}
                  onChange={(event) => setSurvey(event.target.checked)}
                />

                <Button
                  fullWidth
                  size="lg"
                  icon={<Plus className="h-4 w-4" />}
                  loading={create.pending}
                  onClick={submit}
                  disabled={!name.trim()}
                >
                  Create experiment
                </Button>
              </div>
            </RequireRole>
          </CardBody>
        </Card>

        <Card className="h-fit">
          <CardHeader
            title="Experiments"
            actions={<Badge tone="neutral">{(experiments.data ?? []).length} total</Badge>}
          />
          {experiments.loading ? <SkeletonTable rows={4} columns={4} /> : null}
          {experiments.error ? (
            <ErrorState error={experiments.error} onRetry={experiments.refresh} />
          ) : null}
          {experiments.data && experiments.data.length === 0 ? (
            <EmptyState
              icon={<Users className="h-6 w-6" />}
              title="No experiments yet"
              description="Create one to collect real classroom data alongside the simulations."
            />
          ) : null}
          {experiments.data && experiments.data.length > 0 ? (
            <DataTable
              columns={columns}
              rows={experiments.data}
              rowKey={(row) => row.id}
              caption="All experiments"
              onRowClick={(row) => navigate(`/experiments/${row.id}`)}
            />
          ) : null}
        </Card>
      </div>
    </>
  );
}
