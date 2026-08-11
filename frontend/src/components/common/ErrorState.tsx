import { AlertTriangle, RefreshCw, ServerCrash } from "lucide-react";
import type { ApiError } from "@/types";
import { Button } from "./Button";

interface ErrorStateProps {
  error: ApiError;
  onRetry?: () => void;
  title?: string;
}

/**
 * Renders a failed request in language a user can act on. A dropped
 * connection is called out separately from a rejected request, because the
 * fix is completely different.
 */
export function ErrorState({ error, onRetry, title }: ErrorStateProps) {
  const isOffline = error.isNetworkError;

  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center"
    >
      <span
        className={
          isOffline
            ? "rounded-full bg-amber-50 p-3 text-amber-600"
            : "rounded-full bg-red-50 p-3 text-red-600"
        }
        aria-hidden
      >
        {isOffline ? <ServerCrash className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
      </span>

      <h3 className="text-sm font-semibold text-lab-900">
        {title ?? (isOffline ? "Backend unreachable" : "Something went wrong")}
      </h3>

      <p className="max-w-lg text-sm text-slate-600">{error.message}</p>

      {error.details.length > 0 ? (
        <ul className="max-w-lg list-inside list-disc space-y-0.5 text-left text-xs text-slate-500">
          {error.details.map((detail, index) => (
            <li key={index}>{detail}</li>
          ))}
        </ul>
      ) : null}

      {isOffline ? (
        <p className="max-w-lg rounded-lg bg-lab-100 px-3 py-2 font-mono text-xs text-lab-700">
          uvicorn app.main:app --reload
        </p>
      ) : null}

      {onRetry ? (
        <Button
          variant="secondary"
          size="sm"
          icon={<RefreshCw className="h-4 w-4" />}
          onClick={onRetry}
        >
          Try again
        </Button>
      ) : null}
    </div>
  );
}
