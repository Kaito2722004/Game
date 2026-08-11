import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BrainCircuit } from "lucide-react";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/common/Skeleton";
import { Tabs, type TabItem } from "@/components/common/Tabs";
import { ConceptCard, CONCEPTS } from "@/components/game/ConceptCard";
import { PayoffMatrixGrid } from "@/components/game/PayoffMatrixGrid";
import { PageHeader } from "@/components/layout/PageHeader";
import { useGameAnalysis } from "@/hooks";
import {
  ConditionsPanel,
  DominancePanel,
  NashPanel,
  ParetoPanel,
} from "@/features/gameTheory/AnalysisPanels";
import type { PayoffMatrixInput } from "@/types";

const CLASSIC: PayoffMatrixInput = {
  cc: { player_a_payoff: 3, player_b_payoff: 3 },
  cd: { player_a_payoff: 0, player_b_payoff: 5 },
  dc: { player_a_payoff: 5, player_b_payoff: 0 },
  dd: { player_a_payoff: 1, player_b_payoff: 1 },
};

const TABS: TabItem[] = [
  { id: "dilemma", label: "The dilemma" },
  { id: "matrix", label: "Payoff matrix" },
  { id: "dominant", label: "Dominant strategy" },
  { id: "nash", label: "Nash equilibrium" },
  { id: "pareto", label: "Pareto comparison" },
  { id: "repeated", label: "Repeated games" },
  { id: "tft", label: "Tit-for-Tat" },
  { id: "axelrod", label: "Axelrod tournament" },
];

/**
 * The teaching page.
 *
 * Explanations are written for a first encounter with the subject, and every
 * concrete claim about the classic matrix comes from a live backend analysis
 * rather than from text typed into this file.
 */
export function GameTheoryPage() {
  const [tab, setTab] = useState("dilemma");
  const { analysis, loading, error, refresh } = useGameAnalysis(CLASSIC, 0);

  return (
    <>
      <PageHeader
        title="Game Theory"
        description="The ideas behind the Prisoner's Dilemma, explained from scratch and verified against the backend's analysis of the classic matrix."
        icon={<BrainCircuit className="h-5 w-5" />}
      />

      <Tabs items={TABS} active={tab} onChange={setTab} className="mb-5" />

      {error ? (
        <Card>
          <ErrorState error={error} onRetry={refresh} />
        </Card>
      ) : null}

      {tab === "dilemma" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="What is the Prisoner's Dilemma?" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-slate-700">
              <p>
                Two people are questioned separately about a crime they committed
                together. Each can stay silent (<strong>cooperate</strong> with the other
                prisoner) or testify against the other (<strong>defect</strong>). Neither
                knows what the other will do.
              </p>
              <p>
                If both stay silent, the police can only prove a minor charge and both get
                a light sentence. If one testifies while the other stays silent, the
                informer walks free and the silent one takes the heaviest sentence. If both
                testify, both are convicted, though less severely than the lone silent one.
              </p>
              <p>
                The same structure appears far beyond prisons: arms races, price wars,
                overfishing, and sharing work in a group project all have this shape.
              </p>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Why it is a dilemma" />
            <CardBody className="space-y-3">
              <p className="text-sm leading-relaxed text-slate-700">
                Whatever the other person does, defecting pays you more. So a purely
                self-interested player defects — and if both reason that way, both end up
                worse off than if they had cooperated. Rational individual choices produce
                a collectively poor result.
              </p>
              <ConceptCard {...CONCEPTS.dominantStrategy} />
              <ConceptCard {...CONCEPTS.paretoInferior} />
            </CardBody>
          </Card>
        </div>
      ) : null}

      {tab === "matrix" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader
              title="Reading the payoff matrix"
              description="The classic matrix used throughout this project"
            />
            <CardBody className="space-y-4">
              <PayoffMatrixGrid matrix={CLASSIC} analysis={analysis} />
              <p className="text-sm leading-relaxed text-slate-700">
                Each cell holds two numbers: what Player A earns, then what Player B
                earns. Player A picks a row, Player B picks a column, and they choose at
                the same time without seeing each other&apos;s choice.
              </p>
              <Link
                to="/payoff-matrix"
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
              >
                Try editing the numbers yourself
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </CardBody>
          </Card>

          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <ConceptCard {...CONCEPTS.temptation} />
              <ConceptCard {...CONCEPTS.reward} />
              <ConceptCard {...CONCEPTS.punishment} />
              <ConceptCard {...CONCEPTS.sucker} />
            </div>
            {loading && !analysis ? <Skeleton className="h-48 w-full" /> : null}
            {analysis ? <ConditionsPanel analysis={analysis} /> : null}
          </div>
        </div>
      ) : null}

      {tab === "dominant" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="What a dominant strategy is" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-slate-700">
              <p>
                Work through it from Player A&apos;s point of view. Suppose B cooperates:
                A earns 3 by cooperating, or 5 by defecting — defecting is better. Now
                suppose B defects: A earns 0 by cooperating, or 1 by defecting —
                defecting is better again.
              </p>
              <p>
                Defecting wins in <em>both</em> cases, so A never needs to guess what B
                will do. That is what makes it dominant, and by symmetry the same holds
                for B.
              </p>
              <ConceptCard {...CONCEPTS.dominantStrategy} />
            </CardBody>
          </Card>
          {loading && !analysis ? <Skeleton className="h-64 w-full" /> : null}
          {analysis ? <DominancePanel analysis={analysis} /> : null}
        </div>
      ) : null}

      {tab === "nash" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="What a Nash equilibrium is" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-slate-700">
              <p>
                An outcome is a Nash equilibrium when neither player regrets their own
                choice, given what the other did. Nobody can do better by changing their
                move alone.
              </p>
              <p>
                In the classic matrix that point is mutual defection. If both are
                defecting and you switch to cooperating on your own, you drop from 1 to 0
                — so you stay. The same is true for your opponent, which is exactly why
                the outcome is stable.
              </p>
              <p>
                Stability is not the same as goodness: an equilibrium can be a place
                neither player wanted to end up.
              </p>
              <ConceptCard {...CONCEPTS.nashEquilibrium} />
            </CardBody>
          </Card>
          {loading && !analysis ? <Skeleton className="h-64 w-full" /> : null}
          {analysis ? <NashPanel analysis={analysis} /> : null}
        </div>
      ) : null}

      {tab === "pareto" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Comparing outcomes for everyone" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-slate-700">
              <p>
                Mutual defection pays 1 each. Mutual cooperation pays 3 each. Both players
                prefer the second, so the equilibrium is not where they would collectively
                choose to be.
              </p>
              <p>
                That is the heart of the dilemma: the stable outcome and the good outcome
                are different cells of the same table, and individual reasoning drives
                players towards the worse one.
              </p>
              <ConceptCard {...CONCEPTS.paretoOptimal} />
              <ConceptCard {...CONCEPTS.paretoInferior} />
            </CardBody>
          </Card>
          {loading && !analysis ? <Skeleton className="h-64 w-full" /> : null}
          {analysis ? <ParetoPanel analysis={analysis} /> : null}
        </div>
      ) : null}

      {tab === "repeated" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Playing more than once" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-slate-700">
              <p>
                Played once, there is no reason to cooperate. Played repeatedly against
                the same person, what you do now changes how they treat you later — a
                defection today can cost you their cooperation for many rounds.
              </p>
              <p>
                There is a catch when the number of rounds is known in advance. In the
                final round there is no future left to protect, so defection is safe.
                Knowing that, the second-to-last round has nothing to protect either, and
                the reasoning unravels backwards through the whole game. This is the
                backward-induction problem the textbook discusses.
              </p>
              <p>
                When continuation is uncertain — you might meet again, you might not —
                that unravelling has no last round to start from, and cooperation can
                survive. The match simulator lets you set exactly that continuation
                probability.
              </p>
              <ConceptCard {...CONCEPTS.repeatedGame} />
              <ConceptCard {...CONCEPTS.shadowOfTheFuture} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Try it" />
            <CardBody className="space-y-3 text-sm text-slate-700">
              <p>
                Run the same pair of strategies with a fixed length, then with a
                continuation probability, and compare how the match plays out.
              </p>
              <Link
                to="/match-simulator"
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
              >
                Open the match simulator
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </CardBody>
          </Card>
        </div>
      ) : null}

      {tab === "tft" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Tit-for-Tat" description="Two rules, and that is all" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-slate-700">
              <ol className="list-inside list-decimal space-y-1 font-medium text-lab-900">
                <li>Cooperate in the first round.</li>
                <li>After that, copy whatever the opponent did last round.</li>
              </ol>
              <p>
                Four properties are usually singled out when discussing why it does well
                in repeated play:
              </p>
              <ul className="space-y-2">
                <li>
                  <strong>Nice</strong> — it never defects first, so it can build
                  cooperation with anyone willing to reciprocate.
                </li>
                <li>
                  <strong>Retaliatory</strong> — it answers a defection immediately, so it
                  cannot be exploited round after round.
                </li>
                <li>
                  <strong>Forgiving</strong> — one cooperative move from the opponent is
                  enough to restore cooperation.
                </li>
                <li>
                  <strong>Clear</strong> — its rule is easy to work out, so opponents can
                  see that cooperating pays.
                </li>
              </ul>
              <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-900">
                This does not mean Tit-for-Tat is universally best. How it places depends
                on the payoff matrix and on which opponents are in the field. Run a
                tournament and see what actually happens.
              </p>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="See it play" />
            <CardBody className="space-y-3 text-sm text-slate-700">
              <p>
                Against Always Defect over 10 rounds, Tit-for-Tat loses the first round
                and then matches defection for the rest. Against another nice strategy it
                cooperates from start to finish.
              </p>
              <Link
                to="/strategies"
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
              >
                Browse all six strategies
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </CardBody>
          </Card>
        </div>
      ) : null}

      {tab === "axelrod" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Axelrod-style tournaments" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-slate-700">
              <p>
                Robert Axelrod invited researchers to submit strategies for the repeated
                Prisoner&apos;s Dilemma, then had every entry play every other entry over
                many rounds and added up the points.
              </p>
              <p>
                The tournament in this project follows the same design: each selected
                strategy meets each other one, matches run for a configurable number of
                rounds, and strategies are ranked by total score.
              </p>
              <p>
                A key lesson from that setup is that winning individual matches and
                winning the tournament are different things. A strategy that draws
                repeatedly at a high score can finish above one that wins every match at a
                low score.
              </p>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Run your own" />
            <CardBody className="space-y-3 text-sm text-slate-700">
              <p>
                Pick the strategies, the number of rounds and the payoff matrix, then let
                the backend simulate every pairing and rank the field.
              </p>
              <Link
                to="/tournament"
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
              >
                Go to the tournament page
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </CardBody>
          </Card>
        </div>
      ) : null}
    </>
  );
}
