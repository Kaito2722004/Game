import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { BarChart3, PlayCircle, Plus, Shuffle, Trash2, Users } from "lucide-react";
import { experimentApi } from "@/api/experimentApi";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { TextField } from "@/components/common/Field";
import { SkeletonStats } from "@/components/common/Skeleton";
import { StatCard } from "@/components/common/StatCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { useApiAction, useExperiment, useExperimentResults, useParticipants } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import { RequireRole } from "@/features/auth/RequireRole";
import { ExperimentStatusBadge } from "@/features/tournament/StatusBadge";

/** Set up one experiment: participants, pairing, and the link into play. */
export function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const experiment = useExperiment(id);
  const participants = useParticipants(id);
  const results = useExperimentResults(id);

  const [code, setCode] = useState("");
  const [displayName, setDisplayName] = useState("");

  const addParticipant = useApiAction(experimentApi.addParticipant);
  const removeParticipant = useApiAction(experimentApi.removeParticipant);
  const startExperiment = useApiAction(experimentApi.start);

  const isDraft = experiment.data?.status === "DRAFT";

  const add = async () => {
    if (!id || !code.trim()) return;
    const created = await addParticipant.execute(id, {
      code: code.trim(),
      display_name: displayName.trim() || null,
    });
    if (created) {
      toast.success("Participant added", created.code);
      setCode("");
      setDisplayName("");
      void participants.refresh();
      void experiment.refresh();
    } else if (addParticipant.error) {
      toast.apiError(addParticipant.error, "Could not add the participant");
    }
  };

  const remove = async (participantId: string, participantCode: string) => {
    if (!id) return;
    const outcome = await removeParticipant.execute(id, participantId);
    if (outcome !== null) {
      toast.success("Participant removed", participantCode);
      void participants.refresh();
      void experiment.refresh();
    } else if (removeParticipant.error) {
      toast.apiError(removeParticipant.error, "Could not remove the participant");
    }
  };

  const start = async () => {
    if (!id) return;
    const outcome = await startExperiment.execute(id, null);
    if (outcome) {
      toast.success(
        "Experiment started",
        `${outcome.pairs.length} pairs formed. Rounds can now be recorded.`,
      );
      await experiment.refresh();
      await results.refresh();
      navigate(`/experiments/${id}/play`);
    } else if (startExperiment.error) {
      toast.apiError(startExperiment.error, "Could not start the experiment");
    }
  };

  if (experiment.loading) {
    return (
      <>
        <PageHeader title="Experiment" icon={<Users className="h-5 w-5" />} />
        <SkeletonStats count={4} />
      </>
    );
  }

  if (experiment.error) {
    return (
      <>
        <PageHeader title="Experiment" icon={<Users className="h-5 w-5" />} />
        <Card>
          <ErrorState error={experiment.error} onRetry={experiment.refresh} />
        </Card>
      </>
    );
  }

  if (!experiment.data) return null;

  const detail = experiment.data;
  const people = participants.data ?? [];
  const pairs = results.data?.matches ?? [];

  return (
    <>
      <PageHeader
        title={detail.name}
        description={detail.description ?? undefined}
        icon={<Users className="h-5 w-5" />}
        breadcrumbs={[
          { label: "Experiments", to: "/experiments" },
          { label: detail.name },
        ]}
        actions={
          <>
            <ExperimentStatusBadge status={detail.status} />
            {detail.status !== "DRAFT" ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<PlayCircle className="h-4 w-4" />}
                  onClick={() => navigate(`/experiments/${detail.id}/play`)}
                >
                  Play screen
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<BarChart3 className="h-4 w-4" />}
                  onClick={() => navigate(`/experiments/${detail.id}/results`)}
                >
                  Results
                </Button>
              </>
            ) : null}
            {isDraft ? (
              <RequireRole roles={["ADMIN", "TEACHER"]} fallback={null}>
                <Button
                  size="sm"
                  icon={<Shuffle className="h-4 w-4" />}
                  loading={startExperiment.pending}
                  onClick={start}
                  disabled={people.length < 2}
                >
                  Randomise pairs and start
                </Button>
              </RequireRole>
            ) : null}
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Participants" value={detail.participant_count} />
        <StatCard label="Pairs" value={detail.pair_count} />
        <StatCard label="Rounds per pair" value={detail.rounds} />
        <StatCard
          label="Trust survey"
          value={detail.trust_survey_enabled ? "Enabled" : "Disabled"}
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader
            title="Participants"
            description={
              isDraft
                ? "Add everyone taking part, then randomise the pairing."
                : "The roster is fixed once the experiment has started."
            }
            actions={<Badge tone="neutral">{people.length}</Badge>}
          />
          <CardBody className="space-y-4">
            {isDraft ? (
              <RequireRole roles={["ADMIN", "TEACHER"]} fallback={null}>
                <div className="flex flex-wrap items-end gap-2">
                  <div className="min-w-28 flex-1">
                    <TextField
                      label="Code"
                      value={code}
                      onChange={(event) => setCode(event.target.value)}
                      placeholder="S01"
                      hint="A short identifier, unique within this experiment. Used in place of a name when anonymous mode is on."
                    />
                  </div>
                  <div className="min-w-36 flex-1">
                    <TextField
                      label="Display name"
                      value={displayName}
                      onChange={(event) => setDisplayName(event.target.value)}
                      placeholder="Optional"
                    />
                  </div>
                  <Button
                    icon={<Plus className="h-4 w-4" />}
                    loading={addParticipant.pending}
                    onClick={add}
                    disabled={!code.trim()}
                  >
                    Add
                  </Button>
                </div>
              </RequireRole>
            ) : null}

            {people.length === 0 ? (
              <EmptyState
                icon={<Users className="h-6 w-6" />}
                title="No participants yet"
                description="Add at least two people before starting the session."
              />
            ) : (
              <ul className="divide-y divide-lab-100">
                {people.map((person) => (
                  <li key={person.id} className="flex items-center justify-between gap-3 py-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-lab-900">{person.code}</p>
                      {person.display_name && !detail.anonymous_mode ? (
                        <p className="text-xs text-slate-500">{person.display_name}</p>
                      ) : null}
                    </div>
                    {isDraft ? (
                      <RequireRole roles={["ADMIN", "TEACHER"]} fallback={null}>
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Trash2 className="h-4 w-4" />}
                          onClick={() => remove(person.id, person.code)}
                        >
                          <span className="sr-only">Remove {person.code}</span>
                        </Button>
                      </RequireRole>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}

            {isDraft && people.length % 2 === 1 && people.length > 0 ? (
              <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-900">
                There is an odd number of participants, so one person will be left
                unpaired when the session starts.
              </p>
            ) : null}
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="Pairs"
            description={
              isDraft
                ? "Pairs are formed randomly when the experiment starts."
                : "Each pair plays the full set of rounds together."
            }
          />
          <CardBody>
            {pairs.length === 0 ? (
              <EmptyState
                icon={<Shuffle className="h-6 w-6" />}
                title="No pairs yet"
                description="Start the experiment to randomise participants into pairs."
              />
            ) : (
              <ul className="space-y-2">
                {pairs.map((pair) => (
                  <li
                    key={pair.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-lab-200 p-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-lab-900">
                        Pair {pair.pair_number}: {pair.participant_a_label} vs{" "}
                        {pair.participant_b_label}
                      </p>
                      <p className="text-xs text-slate-500">
                        {pair.rounds_recorded} of {detail.rounds} rounds recorded
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm tabular-nums">
                        {pair.player_a_score} – {pair.player_b_score}
                      </span>
                      {pair.is_complete ? (
                        <Badge tone="success">Complete</Badge>
                      ) : (
                        <Badge tone="neutral">In progress</Badge>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>
    </>
  );
}
