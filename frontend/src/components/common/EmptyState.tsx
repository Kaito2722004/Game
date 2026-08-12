import type { ReactNode } from "react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      <span className="rounded-full bg-lab-100 p-3 text-lab-500" aria-hidden>
        {icon ?? <Inbox className="h-6 w-6" />}
      </span>
      <h3 className="text-sm font-semibold text-lab-900">{title}</h3>
      {description ? <p className="max-w-md text-sm text-lab-700">{description}</p> : null}
      {action}
    </div>
  );
}
