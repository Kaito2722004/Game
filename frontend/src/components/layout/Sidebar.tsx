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
          className="fixed inset-0 z-30 animate-fade-in bg-black/70 lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      ) : null}

      <aside
        id="app-sidebar"
        aria-label="Main navigation"
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col",
          "border-r border-lab-250 bg-lab-75/95 backdrop-blur-xl",
          "transition-transform duration-200 lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between gap-2 border-b border-lab-250 px-5 py-4">
          <NavLink to="/dashboard" className="group flex items-center gap-2.5" onClick={onClose}>
            <span
              className="rounded-xl bg-gradient-to-br from-violet-600 to-purple-500 p-2 text-white shadow-[0_4px_16px_-4px_rgb(139_92_246/0.6)] transition-transform group-hover:scale-105"
              aria-hidden
            >
              <Dices className="h-5 w-5" />
            </span>
            <span>
              <span className="block text-sm font-semibold text-white">Game Theory Lab</span>
              <span className="block text-[11px] text-lab-500">Prisoner&apos;s Dilemma</span>
            </span>
          </NavLink>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation"
            className="rounded-lg p-1 text-lab-500 transition-colors hover:bg-lab-200 hover:text-white lg:hidden"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.heading} className="mb-5">
              <h2 className="px-3 pb-1.5 text-[10px] font-semibold tracking-[0.12em] text-lab-500 uppercase">
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
                          "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium",
                          "transition-all duration-200",
                          isActive
                            ? cn(
                                "bg-gradient-to-r from-violet-600/90 to-purple-500/70 text-white",
                                "shadow-[0_4px_18px_-6px_rgb(139_92_246/0.7)]",
                              )
                            : "text-lab-600 hover:bg-lab-200/70 hover:text-lab-900",
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          {/* Left rail marker, so the active item is legible
                              without relying on the gradient alone. */}
                          {isActive ? (
                            <span
                              className="absolute top-1/2 -left-3 h-6 w-1 -translate-y-1/2 rounded-r-full bg-violet-400"
                              aria-hidden
                            />
                          ) : null}
                          <item.icon
                            className={cn(
                              "h-4 w-4 shrink-0 transition-colors",
                              isActive ? "text-white" : "text-lab-500 group-hover:text-violet-300",
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

        <div className="border-t border-lab-250 px-5 py-3">
          <p className="text-[11px] leading-relaxed text-lab-500">
            All game-theoretic results are computed by the FastAPI backend.
          </p>
        </div>
      </aside>
    </>
  );
}
