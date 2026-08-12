import { useState } from "react";
import { Grid2x2, RotateCcw, Save } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardBody, CardHeader } from "@/components/common/Card";
import { Dialog } from "@/components/common/Dialog";
import { ErrorState } from "@/components/common/ErrorState";
import { SelectField, TextField } from "@/components/common/Field";
import { Skeleton } from "@/components/common/Skeleton";
import { Spinner } from "@/components/common/Spinner";
import { PayoffMatrixGrid } from "@/components/game/PayoffMatrixGrid";
import { PageHeader } from "@/components/layout/PageHeader";
import { payoffMatrixApi } from "@/api/payoffMatrixApi";
import { useApiAction, useGameAnalysis, usePayoffMatrices } from "@/hooks";
import { useToast } from "@/context/ToastContext";
import { RequireRole } from "@/features/auth/RequireRole";
import {
  ConditionsPanel,
  DominancePanel,
  NashPanel,
  ParetoPanel,
  SummaryPanel,
} from "@/features/gameTheory/AnalysisPanels";
import type { Outcome, PayoffMatrix, PayoffMatrixInput } from "@/types";
import { OUTCOME_DESCRIPTIONS, OUTCOME_LABELS } from "@/utils/game";

const CLASSIC_MATRIX: PayoffMatrixInput = {
  cc: { player_a_payoff: 3, player_b_payoff: 3 },
  cd: { player_a_payoff: 0, player_b_payoff: 5 },
  dc: { player_a_payoff: 5, player_b_payoff: 0 },
  dd: { player_a_payoff: 1, player_b_payoff: 1 },
};

function toInput(stored: PayoffMatrix): PayoffMatrixInput {
  return { cc: stored.cc, cd: stored.cd, dc: stored.dc, dd: stored.dd };
}

/**
 * Edit a 2x2 matrix and watch the backend re-analyse it.
 *
 * Nothing on this page is precomputed for the classic matrix: change a number
 * and the equilibrium, dominance and Pareto results all follow whatever the
 * API returns for the new values.
 */
export function PayoffMatrixPage() {
  const [matrix, setMatrix] = useState<PayoffMatrixInput>(CLASSIC_MATRIX);
  const [selectedCell, setSelectedCell] = useState<Outcome | null>(null);
  const [saveOpen, setSaveOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const stored = usePayoffMatrices();
  const { analysis, loading, error, refresh } = useGameAnalysis(matrix);
  const toast = useToast();
  const saveAction = useApiAction(payoffMatrixApi.create);

  const updateCell = (outcome: Outcome, player: "a" | "b", value: number) => {
    const key = outcome.toLowerCase() as keyof PayoffMatrixInput;
    setMatrix((current) => ({
      ...current,
      [key]: {
        ...current[key],
        [player === "a" ? "player_a_payoff" : "player_b_payoff"]: value,
      },
    }));
  };

  const loadStored = (id: string) => {
    const found = stored.data?.find((item) => item.id === id);
    if (found) setMatrix(toInput(found));
  };

  const save = async () => {
    const created = await saveAction.execute({
      name: name.trim(),
      description: description.trim() || null,
      ...matrix,
    });
    if (created) {
      toast.success("Matrix saved", `"${created.name}" is now available to simulations.`);
      setSaveOpen(false);
      setName("");
      setDescription("");
      void stored.refresh();
    } else if (saveAction.error) {
      toast.apiError(saveAction.error, "Could not save the matrix");
    }
  };

  const selectedAnalysis = selectedCell
    ? analysis?.pareto_analysis.find((entry) => entry.outcome === selectedCell)
    : undefined;
  const selectedIsNash = selectedCell
    ? analysis?.nash_equilibria.some((entry) => entry.outcome === selectedCell)
    : false;

  return (
    <>
      <PageHeader
        title="Payoff Matrix"
        description="Change any payoff and the backend re-analyses the game. Click a cell for details."
        icon={<Grid2x2 className="h-5 w-5" />}
        actions={
          <>
            <Button
              variant="secondary"
              size="sm"
              icon={<RotateCcw className="h-4 w-4" />}
              onClick={() => setMatrix(CLASSIC_MATRIX)}
            >
              Reset to classic
            </Button>
            <RequireRole roles={["ADMIN", "TEACHER"]} fallback={null}>
              <Button size="sm" icon={<Save className="h-4 w-4" />} onClick={() => setSaveOpen(true)}>
                Save matrix
              </Button>
            </RequireRole>
          </>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader
            title="The matrix"
            description="Player A's payoff first, then Player B's"
            actions={loading ? <Spinner label="Analysing" /> : null}
          />
          <CardBody className="space-y-4">
            {stored.data && stored.data.length > 0 ? (
              <SelectField
                label="Load a stored matrix"
                defaultValue=""
                onChange={(event) => loadStored(event.target.value)}
                help="Saved matrices come from the backend and can be reused in simulations."
              >
                <option value="">Custom (editing below)</option>
                {stored.data.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                    {item.is_default ? " (default)" : ""}
                  </option>
                ))}
              </SelectField>
            ) : null}

            <PayoffMatrixGrid
              matrix={matrix}
              analysis={analysis}
              editable
              onCellChange={updateCell}
              onCellClick={setSelectedCell}
              selected={selectedCell}
            />

            {analysis ? <SummaryPanel analysis={analysis} /> : null}
          </CardBody>
        </Card>

        <div className="space-y-4">
          {error ? (
            <Card>
              <ErrorState error={error} onRetry={refresh} title="Could not analyse this matrix" />
            </Card>
          ) : null}

          {loading && !analysis ? (
            <Card>
              <CardBody className="space-y-3">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </CardBody>
            </Card>
          ) : null}

          {analysis ? (
            <>
              <ConditionsPanel analysis={analysis} />
              <DominancePanel analysis={analysis} />
              <NashPanel analysis={analysis} />
              <ParetoPanel analysis={analysis} />
            </>
          ) : null}
        </div>
      </div>

      <Dialog
        open={selectedCell !== null}
        onClose={() => setSelectedCell(null)}
        title={selectedCell ? OUTCOME_LABELS[selectedCell] : ""}
        description={selectedCell ? `Outcome ${selectedCell}` : undefined}
      >
        {selectedCell ? (
          <div className="space-y-3">
            <p className="text-sm leading-relaxed text-lab-800">
              {OUTCOME_DESCRIPTIONS[selectedCell]}
            </p>

            <div className="rounded-lg bg-lab-50 p-3">
              <p className="font-mono text-lg text-lab-900">
                <span className="text-sky-300">
                  {matrix[selectedCell.toLowerCase() as keyof PayoffMatrixInput].player_a_payoff}
                </span>
                <span className="text-lab-500">, </span>
                <span className="text-orange-300">
                  {matrix[selectedCell.toLowerCase() as keyof PayoffMatrixInput].player_b_payoff}
                </span>
              </p>
              <p className="text-xs text-lab-600">Player A payoff, Player B payoff</p>
            </div>

            <div className="flex flex-wrap gap-2">
              {selectedIsNash ? <Badge tone="accent">Nash equilibrium</Badge> : null}
              {selectedAnalysis?.is_pareto_optimal ? (
                <Badge tone="success">Pareto optimal</Badge>
              ) : (
                <Badge tone="warning">Pareto inferior</Badge>
              )}
            </div>

            {selectedAnalysis ? (
              <p className="text-xs leading-relaxed text-lab-700">
                {selectedAnalysis.explanation}
              </p>
            ) : null}

            {selectedCell === "DD" &&
            analysis?.mutual_cooperation_pareto_superior_to_mutual_defection ? (
              <p className="rounded-lg bg-violet-500/10 p-3 text-xs leading-relaxed text-violet-100">
                For this matrix the backend reports that mutual cooperation is
                Pareto-superior to mutual defection: both players would do better at
                (C,C) than here.
              </p>
            ) : null}
          </div>
        ) : null}
      </Dialog>

      <Dialog
        open={saveOpen}
        onClose={() => setSaveOpen(false)}
        title="Save this payoff matrix"
        description="Stored matrices can be selected in the simulator, tournaments and experiments."
        footer={
          <>
            <Button variant="ghost" onClick={() => setSaveOpen(false)}>
              Cancel
            </Button>
            <Button onClick={save} loading={saveAction.pending} disabled={!name.trim()}>
              Save
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <TextField
            label="Name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Softer punishment variant"
          />
          <TextField
            label="Description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Optional"
          />
        </div>
      </Dialog>
    </>
  );
}
