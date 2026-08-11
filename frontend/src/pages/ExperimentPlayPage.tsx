import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowRight, BarChart3, Eye, PlayCircle, RotateCcw } from "lucide-react";
import { experimentApi } from "@/api/experimentApi";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { SelectField } from "@/components/common/Field";
import { SkeletonStats } from "@/components/common/Skeleton";
import { ActionBadge } from "@/components/game/ActionBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { useApiAction, useExperiment, useExperimentResults } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import { HiddenChoicePanel } from "@/features/experiment/HiddenChoicePanel";
import type { Action, HumanRound } from "@/types";
import { OUTCOME_DESCRIPTIONS, OUTCOME_LABELS } from "@/utils/game";

type Phase = "choosing" | "revealed";

/**
 * The classroom play screen.
 *
 * Two players share one screen. Each picks privately; neither selection is
 * displayed until both are in and the teacher presses Reveal. Payoffs are
 * never computed here — the round is sent to the backend, which returns the
 * authoritative payoffs.
 */
export function ExperimentPlayPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const experiment = useExperiment(id);
  const results = useExperimentResults(id);

  const [matchId, setMatchId] = useState("");
  const [choiceA, setChoiceA] = useState<Action | null>(null);
  const [choiceB, setChoiceB] = useState<Action | null>(null);
  const [phase, setPhase] = useState<Phase>("choosing");
  const [lastRound, setLastRound] = useState<HumanRound | null>(null);

  const submitRound = useApiAction(experimentApi.submitRound);

  const matches = useMemo(() => results.data?.matches ?? [], [results.data]);

  // Default to the first pair that still has rounds left.
  useEffect(() => {
    if (matchId || matches.length === 0) return;
    const next = matches.find((match) => !match.is_complete) ?? matches[0];
    setMatchId(next.id);
  }, [matches, matchId]);

  const activeMatch = matches.find((match) => match.id === matchId) ?? null;
  const roundsForMatch = (results.data?.rounds ?? []).filter(
    (round) => round.match_id === matchId,
  );
  const nextRoundNumber = roundsForMatch.length + 1;
  const totalRounds = experiment.data?.rounds ?? 0;
  const matchFinished = nextRoundNumber > totalRounds;

  const resetChoices = () => {
    setChoiceA(null);
    setChoiceB(null);
    setPhase("choosing");
    setLastRound(null);
  };

  const reveal = async () => {
    if (!id || !matchId || !choiceA || !choiceB) return;

    const recorded = await submitRound.execute(id, {
      match_id: matchId,
      round_number: nextRoundNumber,
      player_a_action: choiceA,
      player_b_action: choiceB,
    });

    if (recorded) {
      setLastRound(recorded);
      setPhase("revealed");
      void results.refresh();
    } else if (submitRound.error) {
      toast.apiError(submitRound.error, "Could not record the round");
    }
  };

  const nextRound = () => {
    resetChoices();
  };

  if (experiment.loading) {
    return (
      <>
        <PageHeader title="Classroom play" icon={<PlayCircle className="h-5 w-5" />} />
        <SkeletonStats count={3} />
      </>
    );
  }

  if (experiment.error) {
    return (
      <>
        <PageHeader title="Classroom play" icon={<PlayCircle className="h-5 w-5" />} />
        <Card>
          <ErrorState error={experiment.error} onRetry={experiment.refresh} />
        </Card>
      </>
    );
  }

  if (!experiment.data) return null;
  const detail = experiment.data;

  if (detail.status === "DRAFT") {
    return (
      <>
        <PageHeader
          title="Classroom play"
          icon={<PlayCircle className="h-5 w-5" />}
          breadcrumbs={[
            { label: "Experiments", to: "/experiments" },
            { label: detail.name, to: `/experiments/${detail.id}` },
            { label: "Play" },
          ]}
        />
        <Card>
          <EmptyState
            icon={<PlayCircle className="h-6 w-6" />}
            title="This experiment has not started"
            description="Add participants and start the session to form pairs, then come back here to record rounds."
            action={
              <Button size="sm" onClick={() => navigate(`/experiments/${detail.id}`)}>
                Go to setup
              </Button>
            }
          />
        </Card>
      </>
    );
  }

  const outcome = lastRound
    ? ((lastRound.player_a_action === "COOPERATE" ? "C" : "D") +
        (lastRound.player_b_action === "COOPERATE" ? "C" : "D")) as
        | "CC"
        | "CD"
        | "DC"
        | "DD"
    : null;

  return (
    <>
      <PageHeader
        title="Classroom play"
        description="Both players choose privately. Nothing is shown until both have decided and the round is revealed."
        icon={<PlayCircle className="h-5 w-5" />}
        breadcrumbs={[
          { label: "Experiments", to: "/experiments" },
          { label: detail.name, to: `/experiments/${detail.id}` },
          { label: "Play" },
        ]}
        actions={
          <Button
            variant="secondary"
            size="sm"
            icon={<BarChart3 className="h-4 w-4" />}
            onClick={() => navigate(`/experiments/${detail.id}/results`)}
          >
            Results
          </Button>
        }
      />

      {matches.length === 0 ? (
        <Card>
          <EmptyState
            title="No pairs available"
            description="This experiment has no pairs recorded. Start it from the setup page."
          />
        </Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[20rem_minmax(0,1fr)]">
          <Card className="h-fit">
            <CardHeader title="Pair" description="Choose which pair is playing" />
            <CardBody className="space-y-4">
              <SelectField
                label="Active pair"
                value={matchId}
                onChange={(event) => {
                  setMatchId(event.target.value);
                  resetChoices();
                }}
              >
                {matches.map((match) => (
                  <option key={match.id} value={match.id}>
                    Pair {match.pair_number}: {match.participant_a_label} vs{" "}
                    {match.participant_b_label}
                    {match.is_complete ? " (complete)" : ""}
                  </option>
                ))}
              </SelectField>

              {activeMatch ? (
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Rounds recorded</dt>
                    <dd className="font-mono text-lab-900">
                      {roundsForMatch.length} / {totalRounds}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">{activeMatch.participant_a_label} score</dt>
                    <dd className="font-mono text-lab-900">{activeMatch.player_a_score}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">{activeMatch.participant_b_label} score</dt>
                    <dd className="font-mono text-lab-900">{activeMatch.player_b_score}</dd>
                  </div>
                </dl>
              ) : null}

              <div className="h-2 overflow-hidden rounded-full bg-lab-200">
                <div
                  className="h-full rounded-full bg-indigo-600 transition-all"
                  style={{
                    width: `${totalRounds > 0 ? Math.min(100, (roundsForMatch.length / totalRounds) * 100) : 0}%`,
                  }}
                  role="progressbar"
                  aria-valuenow={roundsForMatch.length}
                  aria-valuemin={0}
                  aria-valuemax={totalRounds}
                  aria-label="Rounds completed for this pair"
                />
              </div>

              {roundsForMatch.length > 0 ? (
                <div>
                  <h3 className="mb-2 text-xs font-semibold tracking-wide text-slate-500 uppercase">
                    History
                  </h3>
                  <ul className="max-h-64 space-y-1 overflow-y-auto">
                    {roundsForMatch.map((round) => (
                      <li
                        key={round.id}
                        className="flex items-center justify-between gap-2 rounded border border-lab-100 px-2 py-1.5 text-xs"
                      >
                        <span className="font-mono text-slate-500">R{round.round_number}</span>
                        <ActionBadge action={round.player_a_action} showLabel={false} />
                        <ActionBadge action={round.player_b_action} showLabel={false} />
                        <span className="font-mono tabular-nums text-slate-600">
                          {round.player_a_payoff}–{round.player_b_payoff}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </CardBody>
          </Card>

          <div className="space-y-4">
            {matchFinished ? (
              <Card>
                <EmptyState
                  title="This pair has finished"
                  description={`All ${totalRounds} rounds have been recorded. Select another pair, or open the results.`}
                  action={
                    <Button
                      size="sm"
                      icon={<BarChart3 className="h-4 w-4" />}
                      onClick={() => navigate(`/experiments/${detail.id}/results`)}
                    >
                      View results
                    </Button>
                  }
                />
              </Card>
            ) : (
              <>
                <Card>
                  <CardHeader
                    title={`Round ${nextRoundNumber} of ${totalRounds}`}
                    description="Each player chooses without seeing the other's decision."
                    actions={
                      <Badge tone={phase === "revealed" ? "success" : "info"}>
                        {phase === "revealed" ? "Revealed" : "Choosing"}
                      </Badge>
                    }
                  />
                  <CardBody className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <HiddenChoicePanel
                        playerLabel={activeMatch?.participant_a_label ?? "Player A"}
                        choice={choiceA}
                        onChoose={setChoiceA}
                        revealed={phase === "revealed"}
                        disabled={phase === "revealed"}
                      />
                      <HiddenChoicePanel
                        playerLabel={activeMatch?.participant_b_label ?? "Player B"}
                        choice={choiceB}
                        onChoose={setChoiceB}
                        revealed={phase === "revealed"}
                        disabled={phase === "revealed"}
                      />
                    </div>

                    <div className="flex flex-wrap items-center justify-center gap-2">
                      {phase === "choosing" ? (
                        <>
                          <Button
                            size="lg"
                            icon={<Eye className="h-4 w-4" />}
                            disabled={!choiceA || !choiceB}
                            loading={submitRound.pending}
                            onClick={reveal}
                          >
                            Reveal choices
                          </Button>
                          <Button
                            variant="ghost"
                            icon={<RotateCcw className="h-4 w-4" />}
                            onClick={resetChoices}
                            disabled={!choiceA && !choiceB}
                          >
                            Clear
                          </Button>
                        </>
                      ) : (
                        <Button
                          size="lg"
                          icon={<ArrowRight className="h-4 w-4" />}
                          onClick={nextRound}
                        >
                          Next round
                        </Button>
                      )}
                    </div>

                    {!choiceA || !choiceB ? (
                      <p className="text-center text-xs text-slate-500">
                        Both players must choose before the round can be revealed.
                      </p>
                    ) : null}
                  </CardBody>
                </Card>

                {phase === "revealed" && lastRound && outcome ? (
                  <Card className="animate-slide-up">
                    <CardHeader
                      title={OUTCOME_LABELS[outcome]}
                      description={`Round ${lastRound.round_number} result`}
                    />
                    <CardBody className="space-y-3">
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="rounded-lg border border-lab-200 p-3">
                          <p className="text-xs text-slate-500">
                            {activeMatch?.participant_a_label ?? "Player A"}
                          </p>
                          <div className="mt-1 flex items-center justify-between">
                            <ActionBadge action={lastRound.player_a_action} size="md" />
                            <span className="font-mono text-xl font-semibold text-lab-900">
                              +{lastRound.player_a_payoff}
                            </span>
                          </div>
                        </div>
                        <div className="rounded-lg border border-lab-200 p-3">
                          <p className="text-xs text-slate-500">
                            {activeMatch?.participant_b_label ?? "Player B"}
                          </p>
                          <div className="mt-1 flex items-center justify-between">
                            <ActionBadge action={lastRound.player_b_action} size="md" />
                            <span className="font-mono text-xl font-semibold text-lab-900">
                              +{lastRound.player_b_payoff}
                            </span>
                          </div>
                        </div>
                      </div>

                      <p className="rounded-lg bg-lab-50 p-3 text-sm leading-relaxed text-slate-700">
                        {OUTCOME_DESCRIPTIONS[outcome]}
                      </p>

                      <p className="text-xs text-slate-500">
                        Payoffs were calculated by the backend from this experiment&apos;s
                        payoff matrix.
                      </p>
                    </CardBody>
                  </Card>
                ) : null}
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
