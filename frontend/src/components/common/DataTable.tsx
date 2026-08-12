import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

export interface Column<T> {
  key: string;
  header: ReactNode;
  /** Cell renderer. Keep it presentational — no computation of results. */
  render: (row: T, index: number) => ReactNode;
  align?: "left" | "right" | "center";
  className?: string;
  /** Hide on narrow screens, where horizontal space is scarce. */
  hideOnMobile?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  caption?: string;
  onRowClick?: (row: T) => void;
  highlightRow?: (row: T) => boolean;
  emptyMessage?: string;
}

const ALIGN = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
} as const;

/**
 * Scrollable, keyboard-navigable table. On small screens the table scrolls
 * horizontally rather than collapsing columns, so the numbers stay comparable.
 */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  caption,
  onRowClick,
  highlightRow,
  emptyMessage = "No rows to display.",
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return <p className="px-5 py-8 text-center text-sm text-lab-600">{emptyMessage}</p>;
  }

  return (
    <div className="table-scroll">
      <table className="w-full min-w-[36rem] border-collapse text-sm">
        {caption ? <caption className="sr-only">{caption}</caption> : null}
        <thead>
          <tr className="border-b border-lab-250 bg-lab-50/70">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn(
                  "px-3 py-2.5 text-xs font-semibold tracking-wide text-lab-700 uppercase",
                  ALIGN[column.align ?? "left"],
                  column.hideOnMobile && "hidden md:table-cell",
                  column.className,
                )}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const clickable = Boolean(onRowClick);
            return (
              <tr
                key={rowKey(row, index)}
                onClick={clickable ? () => onRowClick?.(row) : undefined}
                onKeyDown={
                  clickable
                    ? (event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          onRowClick?.(row);
                        }
                      }
                    : undefined
                }
                tabIndex={clickable ? 0 : undefined}
                role={clickable ? "button" : undefined}
                className={cn(
                  "border-b border-lab-250 transition-colors last:border-0",
                  clickable && "cursor-pointer hover:bg-violet-500/10",
                  highlightRow?.(row) && "bg-violet-500/10",
                )}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={cn(
                      "px-3 py-2.5 text-lab-800",
                      ALIGN[column.align ?? "left"],
                      column.hideOnMobile && "hidden md:table-cell",
                    )}
                  >
                    {column.render(row, index)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
