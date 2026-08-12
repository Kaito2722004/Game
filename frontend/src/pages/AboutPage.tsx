import { BookMarked, ExternalLink } from "lucide-react";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { API_BASE_URL } from "@/api/client";

const CHAPTERS = [
  {
    number: "Chapter 11",
    title: "Nash Equilibria and Non-Cooperative Solutions",
    usedFor:
      "The equilibrium analysis: what it means for no player to be able to improve by changing strategy alone, and how that is found in a 2x2 game.",
  },
  {
    number: "Chapter 12",
    title: "The Prisoner's Dilemma",
    usedFor:
      "The dilemma itself: dominance, the conflict between individual and collective rationality, repeated play, the backward-induction problem, and Axelrod-style tournaments.",
  },
  {
    number: "Chapter 13",
    title: "Application to Social Psychology: Trust, Suspicion, and the F-Scale",
    usedFor:
      "The motivation for the classroom experiment and the trust survey: whether expectations about others relate to how people actually play.",
  },
];

const PROJECT_PARTS = [
  {
    title: "Theoretical analysis",
    description:
      "The backend computes dominance, pure-strategy Nash equilibria and Pareto status from any 2x2 payoff matrix, rather than assuming the classic result.",
  },
  {
    title: "Human classroom experiment",
    description:
      "Participants are paired and play a fixed number of rounds with simultaneous, hidden choices. The backend records every round and computes the payoffs.",
  },
  {
    title: "Repeated-game simulation",
    description:
      "Matches can run for a fixed number of rounds or with a continuation probability, which is how the shadow of the future is modelled here.",
  },
  {
    title: "Axelrod-style tournament",
    description:
      "Every selected strategy plays every other, scores are summed across all matches, and the field is ranked by the simulation itself.",
  },
  {
    title: "Strategy comparison",
    description:
      "Six strategies — Always Cooperate, Always Defect, Tit-for-Tat, Grim Trigger, Tit-for-Two-Tats and Random — with their rules documented alongside their results.",
  },
  {
    title: "Trust and cooperation analysis",
    description:
      "A short survey on expected cooperation and trust, reported next to observed behaviour as a correlation and never as a cause.",
  },
];

export function AboutPage() {
  return (
    <>
      <PageHeader
        title="About / References"
        description="What this project is, and the sources it is built on."
        icon={<BookMarked className="h-5 w-5" />}
      />

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader title="Primary reference" />
          <CardBody className="space-y-4">
            <div className="rounded-lg border border-lab-250 bg-lab-50 p-4">
              <p className="text-sm font-semibold text-lab-950">Philip D. Straffin</p>
              <p className="text-sm italic text-lab-800">Game Theory and Strategy</p>
              <p className="mt-2 text-xs text-lab-600">
                Consult the book itself for exact wording, page numbers and a formal
                citation in the style your department requires. No page numbers are
                reproduced here, because inventing them would be worse than omitting them.
              </p>
            </div>

            <div className="space-y-3">
              {CHAPTERS.map((chapter) => (
                <div key={chapter.number} className="rounded-lg border border-lab-250 p-3">
                  <p className="text-sm font-semibold text-lab-900">
                    {chapter.number} — {chapter.title}
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-lab-700">
                    {chapter.usedFor}
                  </p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader
              title="What this application does"
              description="Six parts, built on the ideas above"
            />
            <CardBody>
              <dl className="space-y-3">
                {PROJECT_PARTS.map((part) => (
                  <div key={part.title}>
                    <dt className="text-sm font-semibold text-lab-900">{part.title}</dt>
                    <dd className="mt-0.5 text-xs leading-relaxed text-lab-700">
                      {part.description}
                    </dd>
                  </div>
                ))}
              </dl>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="How it is put together" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-lab-800">
              <p>
                This interface is a React and TypeScript application. It holds no game
                theory of its own: every equilibrium, dominance result, payoff and ranking
                shown anywhere in the app is computed by the FastAPI backend and simply
                displayed here.
              </p>
              <p>
                That separation is deliberate. It keeps a single source of truth for the
                results, so the numbers in a report cannot depend on which screen produced
                them.
              </p>
              <div className="rounded-lg bg-lab-50 p-3">
                <p className="text-xs text-lab-600">Currently talking to</p>
                <p className="font-mono text-xs break-all text-lab-800">{API_BASE_URL}</p>
              </div>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-sm font-medium text-violet-400 hover:text-violet-300"
              >
                Open the backend API documentation
                <ExternalLink className="h-3.5 w-3.5" aria-hidden />
              </a>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Academic honesty" />
            <CardBody className="space-y-2 text-xs leading-relaxed text-lab-700">
              <p>
                Results shown in this application come from actual simulations and
                recorded classroom data. No ranking, equilibrium or statistic is
                hard-coded.
              </p>
              <p>
                Tit-for-Tat is not claimed to be universally optimal. How each strategy
                places depends on the payoff matrix and on the field of opponents, and the
                tournament decides it.
              </p>
              <p>
                The trust survey is a short instrument written for this project. Any
                relationship it shows is a correlation within a small sample and does not
                establish causation.
              </p>
            </CardBody>
          </Card>
        </div>
      </div>
    </>
  );
}
