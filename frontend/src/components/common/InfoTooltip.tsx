import { useId, useState, type KeyboardEvent } from "react";
import { HelpCircle } from "lucide-react";

interface InfoTooltipProps {
  /** Short explanation aimed at someone meeting the concept for the first time. */
  text: string;
  label?: string;
}

/**
 * Accessible explanation bubble: reachable by keyboard, announced to screen
 * readers via aria-describedby, and dismissible with Escape.
 */
export function InfoTooltip({ text, label = "More information" }: InfoTooltipProps) {
  const [open, setOpen] = useState(false);
  const id = useId();

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "Escape") setOpen(false);
  };

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        aria-label={label}
        aria-describedby={open ? id : undefined}
        aria-expanded={open}
        className="rounded-full text-lab-400 transition-colors hover:text-violet-300"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={() => setOpen((value) => !value)}
        onKeyDown={onKeyDown}
      >
        <HelpCircle className="h-4 w-4" aria-hidden />
      </button>

      {open ? (
        <span
          id={id}
          role="tooltip"
          className="absolute bottom-full left-1/2 z-30 mb-2 w-64 -translate-x-1/2 animate-scale-in rounded-lg bg-lab-950 px-3 py-2 text-xs leading-relaxed font-normal text-white shadow-lg"
        >
          {text}
        </span>
      ) : null}
    </span>
  );
}
