import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  maxWidth?: string;
}

/**
 * Modal dialog with focus management: focus moves into the panel on open,
 * Escape closes it, the page behind cannot scroll, and focus returns to
 * whatever opened it.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  maxWidth = "max-w-lg",
}: DialogProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const previouslyFocused = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
      previouslyFocused?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  // Rendered into document.body on purpose. A `position: fixed` element is
  // positioned against the nearest ancestor with a filter, transform or
  // backdrop-filter rather than the viewport — the translucent top bar uses
  // backdrop-blur, so a dialog opened from there would be trapped inside its
  // 64px height and clipped. A portal sidesteps that entirely, and keeps the
  // dialog above every stacking context on the page.
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4">
      <div
        className="absolute inset-0 animate-fade-in bg-black/70"
        onClick={onClose}
        aria-hidden
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className={
          "relative z-10 max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-lab-100 shadow-xl " +
          "animate-slide-up sm:rounded-2xl " +
          maxWidth
        }
      >
        <header className="flex items-start justify-between gap-4 border-b border-lab-250 px-5 py-4">
          <div>
            <h2 className="text-base font-semibold text-lab-950">{title}</h2>
            {description ? <p className="mt-1 text-sm text-lab-700">{description}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-1 text-lab-400 transition-colors hover:bg-lab-200 hover:text-lab-700"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </header>

        <div className="px-5 py-4">{children}</div>

        {footer ? (
          <footer className="flex justify-end gap-2 border-t border-lab-250 px-5 py-4">
            {footer}
          </footer>
        ) : null}
      </div>
    </div>,
    document.body,
  );
}
