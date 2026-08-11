import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import type { ExperimentStatus, TournamentStatus } from "@/types";

export function StatusBadge({ status }: { status: TournamentStatus }) {
  switch (status) {
    case "COMPLETED":
      return (
        <Badge tone="success" icon={<CheckCircle2 className="h-3 w-3" aria-hidden />}>
          Completed
        </Badge>
      );
    case "RUNNING":
      return (
        <Badge tone="info" icon={<Loader2 className="h-3 w-3 animate-spin" aria-hidden />}>
          Running
        </Badge>
      );
    case "FAILED":
      return (
        <Badge tone="defect" icon={<XCircle className="h-3 w-3" aria-hidden />}>
          Failed
        </Badge>
      );
    default:
      return (
        <Badge tone="neutral" icon={<Circle className="h-3 w-3" aria-hidden />}>
          Pending
        </Badge>
      );
  }
}

export function ExperimentStatusBadge({ status }: { status: ExperimentStatus }) {
  switch (status) {
    case "COMPLETED":
      return (
        <Badge tone="success" icon={<CheckCircle2 className="h-3 w-3" aria-hidden />}>
          Completed
        </Badge>
      );
    case "RUNNING":
      return (
        <Badge tone="info" icon={<Loader2 className="h-3 w-3" aria-hidden />}>
          Running
        </Badge>
      );
    default:
      return (
        <Badge tone="neutral" icon={<Circle className="h-3 w-3" aria-hidden />}>
          Draft
        </Badge>
      );
  }
}
