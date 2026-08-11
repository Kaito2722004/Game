import { NavLink } from "react-router-dom";
import { Dices, X } from "lucide-react";
import { cn } from "@/utils/cn";
import { NAV_SECTIONS } from "./navigation";

interface SidebarProps {
  /** Mobile drawer state. On desktop the sidebar is always visible. */
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open ? (
        <div
          className="fixed inset-0 z-30 animate-fade-in bg-lab-950/40 lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      ) : null}

      <aside
        id="app-sidebar"
        aria-label="Main navigation"
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-lab-200 bg-white",
          "transition-transform duration-200 lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between gap-2 border-b border-lab-200 px-5 py-4">
          <NavLink to="/dashboard" className="flex items-center gap-2.5" onClick={onClose}>
            <span className="rounded-lg bg-indigo-600 p-1.5 text-white" aria-hidden>
              <Dices className="h-5 w-5" />
            </span>
            <span>
              <span className="block text-sm font-semibold text-lab-950">
                Game Theory Lab
              </span>
              <span className="block text-[11px] text-slate-500">Prisoner&apos;s Dilemma</span>
            </span>
          </NavLink>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation"
            className="rounded-lg p-1 text-lab-400 hover:bg-lab-100 hover:text-lab-700 lg:hidden"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.heading} className="mb-5">
              <h2 className="px-3 pb-1.5 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                {section.heading}
              </h2>
              <ul className="space-y-0.5">
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      onClick={onClose}
                      title={item.description}
                      className={({ isActive }) =>
                        cn(
                          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                          isActive
                            ? "bg-indigo-50 text-indigo-700"
                            : "text-lab-700 hover:bg-lab-100 hover:text-lab-900",
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <item.icon
                            className={cn(
                              "h-4 w-4 shrink-0",
                              isActive ? "text-indigo-600" : "text-lab-400",
                            )}
                            aria-hidden
                          />
                          {item.label}
                        </>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <div className="border-t border-lab-200 px-5 py-3">
          <p className="text-[11px] leading-relaxed text-slate-500">
            All game-theoretic results are computed by the FastAPI backend.
          </p>
        </div>
      </aside>
    </>
  );
}
