import { useEffect, useState } from "react";
import { Send, ShieldQuestion } from "lucide-react";
import { surveyApi } from "@/api/surveyApi";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { SelectField } from "@/components/common/Field";
import { StatCard } from "@/components/common/StatCard";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  useApiAction,
  useExperiments,
  useParticipants,
  useTrustSurveyStatistics,
} from "@/hooks";
import { useToast } from "@/context/ToastContext";
import type { SurveyQuestionType } from "@/types";
import { formatCorrelation, formatNumber, formatPercent } from "@/utils/format";

const SCALE = [1, 2, 3, 4, 5];

const QUESTIONS: Record<SurveyQuestionType, { prompt: string; low: string; high: string }> = {
  EXPECTED_COOPERATION: {
    prompt: "How likely do you think your opponent is to cooperate?",
    low: "Very unlikely",
    high: "Very likely",
  },
  TRUST_AFTER: {
    prompt: "How much did you trust your opponent?",
    low: "Not at all",
    high: "Completely",
  },
};

/**
 * The classroom trust survey.
 *
 * Two questions on a 1–5 scale, written for this project. It is not a
 * standardised psychological instrument, and nothing here reproduces the
 * historical F-scale questionnaire.
 */
export function TrustSurveyPage() {
  const toast = useToast();
  const experiments = useExperiments();

  const [experimentId, setExperimentId] = useState("");
  const [participantId, setParticipantId] = useState("");
  const [questionType, setQuestionType] = useState<SurveyQuestionType>("EXPECTED_COOPERATION");
  const [score, setScore] = useState<number | null>(null);

  const participants = useParticipants(experimentId || undefined);
  const statistics = useTrustSurveyStatistics(experimentId || undefined);
  const submit = useApiAction(surveyApi.submit);

  useEffect(() => {
    const list = experiments.data ?? [];
    if (!experimentId && list.length > 0) setExperimentId(list[0].id);
  }, [experiments.data, experimentId]);

  const send = async () => {
    if (!experimentId || !participantId || score === null) return;
    const recorded = await submit.execute({
      experiment_id: experimentId,
      participant_id: participantId,
      question_type: questionType,
      score,
    });

    if (recorded) {
      toast.success("Response recorded", "Thank you.");
      setScore(null);
      void statistics.refresh();
    } else if (submit.error) {
      toast.apiError(submit.error, "Could not record the response");
    }
  };

  const question = QUESTIONS[questionType];

  return (
    <>
      <PageHeader
        title="Trust Survey"
        description="A short classroom survey on expected cooperation and trust, to set alongside what participants actually did."
        icon={<ShieldQuestion className="h-5 w-5" />}
      />

      {(experiments.data ?? []).length === 0 && !experiments.loading ? (
        <Card>
          <EmptyState
            icon={<ShieldQuestion className="h-6 w-6" />}
            title="No experiments available"
            description="Create a classroom experiment first — survey answers are recorded against its participants."
          />
        </Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)]">
          <Card className="h-fit">
            <CardHeader title="Record a response" />
            <CardBody className="space-y-4">
              <SelectField
                label="Experiment"
                value={experimentId}
                onChange={(event) => {
                  setExperimentId(event.target.value);
                  setParticipantId("");
                }}
              >
                <option value="">Select an experiment</option>
                {(experiments.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </SelectField>

              <SelectField
                label="Participant"
                value={participantId}
                onChange={(event) => setParticipantId(event.target.value)}
                disabled={!experimentId || participants.loading}
              >
                <option value="">Select a participant</option>
                {(participants.data ?? []).map((person) => (
                  <option key={person.id} value={person.id}>
                    {person.code}
                  </option>
                ))}
              </SelectField>

              <SelectField
                label="Question"
                value={questionType}
                onChange={(event) => setQuestionType(event.target.value as SurveyQuestionType)}
              >
                <option value="EXPECTED_COOPERATION">Before the game</option>
                <option value="TRUST_AFTER">After the game</option>
              </SelectField>

              <fieldset>
                <legend className="mb-2 text-sm font-medium text-lab-800">
                  {question.prompt}
                </legend>
                <div className="flex gap-2" role="radiogroup" aria-label={question.prompt}>
                  {SCALE.map((value) => (
                    <button
                      key={value}
                      type="button"
                      role="radio"
                      aria-checked={score === value}
                      onClick={() => setScore(value)}
                      className={
                        score === value
                          ? "flex-1 rounded-lg border-2 border-violet-500 bg-violet-500/10 py-3 font-semibold text-violet-300 transition-colors"
                          : "flex-1 rounded-lg border-2 border-lab-250 py-3 font-medium text-lab-700 transition-colors hover:border-lab-300"
                      }
                    >
                      {value}
                    </button>
                  ))}
                </div>
                <div className="mt-1 flex justify-between text-[11px] text-lab-600">
                  <span>1 — {question.low}</span>
                  <span>5 — {question.high}</span>
                </div>
              </fieldset>

              <Button
                fullWidth
                icon={<Send className="h-4 w-4" />}
                loading={submit.pending}
                onClick={send}
                disabled={!experimentId || !participantId || score === null}
              >
                Submit response
              </Button>

              <p className="rounded-lg bg-lab-50 p-3 text-xs leading-relaxed text-lab-700">
                This classroom survey is exploratory and does not establish psychological
                causation.
              </p>
            </CardBody>
          </Card>

          <div className="space-y-4">
            {statistics.error ? (
              <Card>
                <ErrorState error={statistics.error} onRetry={statistics.refresh} />
              </Card>
            ) : null}

            {statistics.data && statistics.data.responses > 0 ? (
              <>
                <div className="grid gap-4 sm:grid-cols-3">
                  <StatCard
                    label="Expected cooperation"
                    value={formatNumber(statistics.data.average_expected_cooperation ?? 0, 2)}
                    footer={`${statistics.data.expected_cooperation_responses} responses`}
                    hint="Average answer to the before-play question, on a 1–5 scale."
                  />
                  <StatCard
                    label="Trust score"
                    value={formatNumber(statistics.data.average_trust_after ?? 0, 2)}
                    footer={`${statistics.data.trust_after_responses} responses`}
                    hint="Average answer to the after-play question, on a 1–5 scale."
                  />
                  <StatCard
                    label="Actual cooperation"
                    value={formatPercent(statistics.data.actual_cooperation_rate)}
                    tone="cooperate"
                    hint="What participants actually did, from the recorded rounds."
                  />
                </div>

                <Card>
                  <CardHeader
                    title="Relationship with observed behaviour"
                    description="Correlation between survey answers and actual cooperation"
                  />
                  <CardBody className="space-y-3">
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-lg border border-lab-250 p-3">
                        <p className="text-xs text-lab-600">
                          Expected cooperation vs actual cooperation
                        </p>
                        <p className="mt-1 font-mono text-2xl font-semibold text-lab-900">
                          {formatCorrelation(statistics.data.correlation_expected_vs_actual)}
                        </p>
                      </div>
                      <div className="rounded-lg border border-lab-250 p-3">
                        <p className="text-xs text-lab-600">
                          Trust after play vs actual cooperation
                        </p>
                        <p className="mt-1 font-mono text-2xl font-semibold text-lab-900">
                          {formatCorrelation(statistics.data.correlation_trust_after_vs_actual)}
                        </p>
                      </div>
                    </div>

                    <p className="rounded-lg bg-amber-400/10 p-3 text-xs leading-relaxed text-amber-200">
                      {statistics.data.interpretation_note}
                    </p>
                  </CardBody>
                </Card>
              </>
            ) : null}

            {statistics.data && statistics.data.responses === 0 ? (
              <Card>
                <EmptyState
                  icon={<ShieldQuestion className="h-6 w-6" />}
                  title="No responses yet"
                  description="Record survey answers on the left and the summary will appear here."
                />
              </Card>
            ) : null}

            <Card>
              <CardHeader title="About this survey" />
              <CardBody className="space-y-3 text-sm leading-relaxed text-lab-800">
                <p>
                  The textbook&apos;s chapter on social psychology connects the
                  Prisoner&apos;s Dilemma to questions of trust and suspicion: whether how
                  much people expect others to cooperate relates to how they themselves
                  behave.
                </p>
                <p>
                  This survey asks two short questions written for this project — one
                  before play and one after. It deliberately does not reproduce the
                  historical F-scale questionnaire discussed in that literature.
                </p>
                <p className="text-xs text-lab-600">
                  With a classroom-sized sample, any relationship found here is a
                  description of these particular participants and nothing more.
                </p>
              </CardBody>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
