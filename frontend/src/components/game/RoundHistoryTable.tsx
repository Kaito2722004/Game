import { useState } from "react";
import { DataTable, type Column } from "@/components/common/DataTable";
import { Button } from "@/components/common/Button";
import type { RoundResult } from "@/types";
import { OUTCOME_LABELS } from "@/utils/game";
import { ActionBadge } from "./ActionBadge";

interface RoundHistoryTableProps {
  rounds: RoundResult[];
  labelA?: string;
  labelB?: string;
  /** Rounds shown before the "show all" control appears. */
  initialLimit?: number;
}

/** Round-by-round history for a match, shared by the simulator and tournaments. */
export function RoundHistoryTable({
  rounds,
  labelA = "Player A",
  labelB = "Player B",
  initialLimit = 20,
}: RoundHistoryTableProps) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? rounds : rounds.slice(0, initialLimit);

  const columns: Column<RoundResult>[] = [
    {
      key: "round",
      header: "Round",
      render: (row) => <span className="font-mono text-xs text-lab-600">{row.round_number}</span>,
    },
    {
      key: "actionA",
      header: `${labelA} action`,
      render: (row) => <ActionBadge action={row.player_a_action} />,
    },
    {
      key: "actionB",
      header: `${labelB} action`,
      render: (row) => <ActionBadge action={row.player_b_action} />,
    },
    {
      key: "payoffA",
      header: `${labelA} payoff`,
      align: "right",
      render: (row) => <span className="font-mono tabular-nums">{row.player_a_payoff}</span>,
    },
    {
      key: "payoffB",
      header: `${labelB} payoff`,
      align: "right",
      render: (row) => <span className="font-mono tabular-nums">{row.player_b_payoff}</span>,
    },
    {
      key: "outcome",
      header: "Outcome",
      hideOnMobile: true,
      render: (row) => (
        <span className="text-xs text-lab-700">{OUTCOME_LABELS[row.outcome]}</span>
      ),
    },
  ];

  return (
    <div>
      <DataTable
        columns={columns}
        rows={visible}
        rowKey={(row) => String(row.round_number)}
        caption="Round by round history of the match"
        emptyMessage="No rounds were played."
      />

      {rounds.length > initialLimit ? (
        <div className="flex justify-center border-t border-lab-250 py-3">
          <Button variant="ghost" size="sm" onClick={() => setShowAll((value) => !value)}>
            {showAll
              ? `Show first ${initialLimit} rounds`
              : `Show all ${rounds.length} rounds`}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
