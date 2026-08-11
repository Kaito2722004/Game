import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { FlaskConical } from "lucide-react";
import { USE_MOCK_API } from "@/api/client";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

/**
 * Application shell: persistent sidebar on desktop, a drawer on mobile, and
 * the routed page in the main region.
 */
export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Close the mobile drawer whenever navigation happens.
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-lab-50">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="lg:pl-72">
        <Topbar onOpenSidebar={() => setSidebarOpen(true)} />

        {USE_MOCK_API ? (
          <div
            role="status"
            className="flex items-center justify-center gap-2 bg-amber-100 px-4 py-2 text-center text-xs font-medium text-amber-900"
          >
            <FlaskConical className="h-4 w-4" aria-hidden />
            Demo Mode — showing sample data from the local mock adapter, not the FastAPI
            backend.
          </div>
        ) : null}

        <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>

        <footer className="mx-auto max-w-7xl px-4 pb-8 sm:px-6 lg:px-8">
          <p className="border-t border-lab-200 pt-4 text-xs text-slate-500">
            University Game Theory project · based on Philip D. Straffin,{" "}
            <cite>Game Theory and Strategy</cite>
          </p>
        </footer>
      </div>
    </div>
  );
}
