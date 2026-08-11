import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import type { ApiError } from "@/types";

export type ToastTone = "success" | "error" | "info";

interface Toast {
  id: number;
  tone: ToastTone;
  title: string;
  description?: string;
}

interface ToastContextValue {
  notify: (tone: ToastTone, title: string, description?: string) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
  /** Convenience for the common "request failed" case. */
  apiError: (error: ApiError, fallbackTitle?: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const TONE_STYLES: Record<ToastTone, { ring: string; icon: ReactNode }> = {
  success: {
    ring: "ring-emerald-200 bg-emerald-50",
    icon: <CheckCircle2 className="h-5 w-5 text-emerald-600" aria-hidden />,
  },
  error: {
    ring: "ring-red-200 bg-red-50",
    icon: <AlertCircle className="h-5 w-5 text-red-600" aria-hidden />,
  },
  info: {
    ring: "ring-blue-200 bg-blue-50",
    icon: <Info className="h-5 w-5 text-blue-600" aria-hidden />,
  },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const notify = useCallback(
    (tone: ToastTone, title: string, description?: string) => {
      const id = nextId.current++;
      setToasts((current) => [...current, { id, tone, title, description }]);
      window.setTimeout(() => dismiss(id), tone === "error" ? 8000 : 4500);
    },
    [dismiss],
  );

  const value = useMemo<ToastContextValue>(
    () => ({
      notify,
      success: (title, description) => notify("success", title, description),
      error: (title, description) => notify("error", title, description),
      info: (title, description) => notify("info", title, description),
      apiError: (error, fallbackTitle = "Request failed") =>
        notify(
          "error",
          error.isNetworkError ? "Backend unreachable" : fallbackTitle,
          [error.message, ...error.details].filter(Boolean).join(" "),
        ),
    }),
    [notify],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}

      <div
        aria-live="polite"
        aria-atomic="false"
        className="pointer-events-none fixed inset-x-4 bottom-4 z-[60] flex flex-col items-center gap-2 sm:inset-x-auto sm:right-4 sm:items-end"
      >
        {toasts.map((toast) => {
          const style = TONE_STYLES[toast.tone];
          return (
            <div
              key={toast.id}
              className={`pointer-events-auto flex w-full max-w-sm animate-slide-up items-start gap-3 rounded-xl px-4 py-3 shadow-lg ring-1 ${style.ring}`}
            >
              {style.icon}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-lab-950">{toast.title}</p>
                {toast.description ? (
                  <p className="mt-0.5 text-xs break-words text-slate-600">{toast.description}</p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                aria-label="Dismiss notification"
                className="rounded p-0.5 text-slate-400 transition-colors hover:text-slate-700"
              >
                <X className="h-4 w-4" aria-hidden />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside a ToastProvider");
  return context;
}
