import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Trophy } from "lucide-react";
import { tournamentApi } from "@/api/tournamentApi";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { DataTable, type Column } from "@/components/common/DataTable";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { CheckboxField, SelectField, TextField } from "@/components/common/Field";
import { SkeletonTable } from "@/components/common/Skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { useApiAction, usePayoffMatrices, useStrategies, useTournaments } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import { RequireRole } from "@/features/auth/RequireRole";
import { StatusBadge } from "@/features/tournament/StatusBadge";
import type { Tournament } from "@/types";
import { formatDate } from "@/utils/format";

const MIN_STRATEGIES = 2;

export function TournamentPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const tournaments = useTournaments();
  const strategies = useStrategies();
  const matrices = usePayoffMatrices();

  const [name, setName] = useState("Axelrod-style round robin");
  const [description, setDescription] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [rounds, setRounds] = useState(100);
  const [repetitions, setRepetitions] = useState(1);
  const [seed, setSeed] = useState("42");
  const [matrixId, setMatrixId] = useState("");
  const [selfPlay, setSelfPlay] = useState(false);
  const [useContinuation, setUseContinuation] = useState(false);
  const [continuation, setContinuation] = useState(0.95);

  const create = useApiAction(tournamentApi.create);

  // Select every strategy by default once the registry has loaded.
  const allIds = (strategies.data ?? []).map((strategy) => strategy.id);
  const effectiveSelection = selected.length > 0 ? selected : allIds;

  const toggle = (id: string) => {
    const base = selected.length > 0 ? selected : allIds;
    setSelected(base.includes(id) ? base.filter((item) => item !== id) : [...base, id]);
  };

  const tooFewStrategies = effectiveSelection.length < MIN_STRATEGIES && !selfPlay;

  const submit = async () => {
    const created = await create.execute({
      name: name.trim(),
      description: description.trim() || null,
      strategy_ids: effectiveSelection,
      rounds_per_match: rounds,
      repetitions,
      seed: seed.trim() === "" ? null : Number(seed),
      continuation_probability: useContinuation ? continuation : null,
      include_self_play: selfPlay,
      payoff_matrix_id: matrixId || undefined,
    });

    if (created) {
      toast.success("Tournament created", "Open it to run the simulation.");
      void tournaments.refresh();
      navigate(`/tournament/${created.id}`);
    } else if (create.error) {
      toast.apiError(create.error, "Could not create the tournament");
    }
  };

  const columns: Column<Tournament>[] = [
    {
      key: "name",
      header: "Tournament",
      render: (row) => (
        <div className="min-w-0">
          <Link
            to={`/tournament/${row.id}`}
            className="font-medium text-violet-300 hover:text-violet-200"
          >
            {row.name}
          </Link>
          <p className="text-xs text-lab-600">{row.strategy_codes.length} strategies</p>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "rounds",
      header: "Rounds",
      align: "right",
      hideOnMobile: true,
      render: (row) => <span className="font-mono text-sm">{row.rounds_per_match}</span>,
    },
    {
      key: "matches",
      header: "Matches",
      align: "right",
      hideOnMobile: true,
      render: (row) => <span className="font-mono text-sm">{row.matches_played}</span>,
    },
    {
      key: "created",
      header: "Created",
      hideOnMobile: true,
      render: (row) => <span className="text-xs text-lab-600">{formatDate(row.created_at)}</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="Tournament"
        description="Set up a round robin where every selected strategy meets every other, then let the backend simulate it."
        icon={<Trophy className="h-5 w-5" />}
      />

      <div className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader
            title="New tournament"
            description="Creating registers the configuration; running it simulates every match."
          />
          <CardBody>
            <RequireRole roles={["ADMIN", "TEACHER"]}>
              <div className="space-y-4">
                <TextField
                  label="Tournament name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />

                <TextField
                  label="Description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Optional"
                />

                <fieldset>
                  <legend className="mb-2 text-sm font-medium text-lab-800">
                    Strategies ({effectiveSelection.length} selected)
                  </legend>
                  {strategies.error ? (
                    <ErrorState error={strategies.error} onRetry={strategies.refresh} />
                  ) : (
                    <div className="grid gap-2">
                      {(strategies.data ?? []).map((strategy) => {
                        const checked = effectiveSelection.includes(strategy.id);
                        return (
                          <label
                            key={strategy.id}
                            className={
                              checked
                                ? "flex cursor-pointer items-start gap-2.5 rounded-lg border-2 border-violet-400 bg-violet-500/10 p-2.5 transition-colors"
                                : "flex cursor-pointer items-start gap-2.5 rounded-lg border-2 border-lab-250 p-2.5 transition-colors hover:border-lab-300"
                            }
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggle(strategy.id)}
                              className="mt-0.5 h-4 w-4 rounded border-lab-300 text-violet-400"
                            />
                            <span className="min-w-0">
                              <span className="block text-sm font-medium text-lab-900">
                                {strategy.name}
                              </span>
                              <span className="block text-xs text-lab-600">
                                {strategy.category === "NICE"
                                  ? "Never defects first"
                                  : strategy.category === "NASTY"
                                    ? "Opens with defection"
                                    : "Uses randomness"}
                              </span>
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  )}
                  {tooFewStrategies ? (
                    <p role="alert" className="mt-2 text-xs font-medium text-rose-300">
                      Select at least {MIN_STRATEGIES} strategies, or enable self-play.
                    </p>
                  ) : null}
                </fieldset>

                <TextField
                  label="Rounds per match"
                  type="number"
                  min={1}
                  max={10000}
                  value={rounds}
                  onChange={(event) => setRounds(Number(event.target.value))}
                />

                <TextField
                  label="Repetitions"
                  type="number"
                  min={1}
                  max={1000}
                  value={repetitions}
                  onChange={(event) => setRepetitions(Number(event.target.value))}
                  hint="Replays the whole round robin. Useful for averaging out luck when a random strategy takes part."
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
                  help="Leave empty for an unseeded run."
                />

                <CheckboxField
                  label="Include self-play"
                  description="Each strategy also plays a copy of itself."
                  checked={selfPlay}
                  onChange={(event) => setSelfPlay(event.target.checked)}
                />

                <div className="space-y-2 rounded-lg border border-lab-250 p-3">
                  <CheckboxField
                    label="Uncertain ending"
                    description="Model the shadow of the future with a continuation probability."
                    checked={useContinuation}
                    onChange={(event) => setUseContinuation(event.target.checked)}
                  />
                  {useContinuation ? (
                    <div>
                      <label htmlFor="t-continuation" className="text-xs font-medium text-lab-700">
                        Continuation probability: {continuation.toFixed(2)}
                      </label>
                      <input
                        id="t-continuation"
                        type="range"
                        min={0}
                        max={1}
                        step={0.01}
                        value={continuation}
                        onChange={(event) => setContinuation(Number(event.target.value))}
                        className="mt-1 w-full accent-violet-500"
                      />
                    </div>
                  ) : null}
                </div>

                <Button
                  fullWidth
                  size="lg"
                  icon={<Plus className="h-4 w-4" />}
                  loading={create.pending}
                  onClick={submit}
                  disabled={!name.trim() || tooFewStrategies}
                >
                  Create tournament
                </Button>
              </div>
            </RequireRole>
          </CardBody>
        </Card>

        <Card className="h-fit">
          <CardHeader
            title="Tournaments"
            description="Open one to run it or review its results"
            actions={
              <Badge tone="neutral">{(tournaments.data ?? []).length} total</Badge>
            }
          />
          {tournaments.loading ? <SkeletonTable rows={4} columns={4} /> : null}
          {tournaments.error ? (
            <ErrorState error={tournaments.error} onRetry={tournaments.refresh} />
          ) : null}
          {tournaments.data && tournaments.data.length === 0 ? (
            <EmptyState
              icon={<Trophy className="h-6 w-6" />}
              title="No tournaments yet"
              description="Create one on the left to compare strategies head to head."
            />
          ) : null}
          {tournaments.data && tournaments.data.length > 0 ? (
            <DataTable
              columns={columns}
              rows={tournaments.data}
              rowKey={(row) => row.id}
              caption="All tournaments"
              onRowClick={(row) => navigate(`/tournament/${row.id}`)}
            />
          ) : null}
        </Card>
      </div>
    </>
  );
}
