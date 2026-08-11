import type { KeyboardEvent, ReactNode } from "react";
import { cn } from "@/utils/cn";

export interface TabItem {
  id: string;
  label: string;
  icon?: ReactNode;
}

interface TabsProps {
  items: TabItem[];
  active: string;
  onChange: (id: string) => void;
  className?: string;
}

/** Tab strip following the WAI-ARIA tabs pattern, with arrow-key navigation. */
export function Tabs({ items, active, onChange, className }: TabsProps) {
  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    event.preventDefault();
    const offset = event.key === "ArrowRight" ? 1 : -1;
    const next = (index + offset + items.length) % items.length;
    onChange(items[next].id);
  };

  return (
    <div
      role="tablist"
      className={cn("flex gap-1 overflow-x-auto border-b border-lab-200", className)}
    >
      {items.map((item, index) => {
        const selected = item.id === active;
        return (
          <button
            key={item.id}
            role="tab"
            type="button"
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(item.id)}
            onKeyDown={(event) => onKeyDown(event, index)}
            className={cn(
              "flex shrink-0 items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
              selected
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-slate-500 hover:border-lab-300 hover:text-lab-800",
            )}
          >
            {item.icon}
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
