import { useLocation, useNavigate } from "react-router-dom";
import { LogIn, LogOut, Menu, ShieldCheck, User as UserIcon } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { useAuth } from "@/context/AuthContext";

interface TopbarProps {
  onOpenSidebar: () => void;
}

export function Topbar({ onOpenSidebar }: TopbarProps) {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Remember where the user was, so signing in returns them to it.
  const goToLogin = () =>
    navigate("/login", { state: { from: location.pathname + location.search } });

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-lab-250 bg-lab-50/80 px-4 backdrop-blur-xl sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenSidebar}
          aria-label="Open navigation"
          aria-controls="app-sidebar"
          className="rounded-lg p-2 text-lab-600 transition-colors hover:bg-lab-200 lg:hidden"
        >
          <Menu className="h-5 w-5" aria-hidden />
        </button>

        <div className="hidden sm:block">
          <p className="text-sm font-semibold text-lab-950">
            Prisoner&apos;s Dilemma Strategy Tournament
          </p>
          <p className="text-[11px] text-lab-600">
            Theory, simulation and classroom experiment
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isAuthenticated && user ? (
          <>
            <div className="hidden text-right sm:block">
              <p className="text-xs font-medium text-lab-900">{user.full_name}</p>
              <p className="text-[11px] text-lab-600">{user.email}</p>
            </div>
            <Badge
              tone={user.role === "STUDENT" ? "neutral" : "accent"}
              icon={<ShieldCheck className="h-3 w-3" aria-hidden />}
            >
              {user.role}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              icon={<LogOut className="h-4 w-4" />}
              onClick={logout}
            >
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          </>
        ) : (
          <>
            <Badge tone="neutral" icon={<UserIcon className="h-3 w-3" aria-hidden />}>
              Signed out
            </Badge>
            <Button
              variant="secondary"
              size="sm"
              icon={<LogIn className="h-4 w-4" />}
              onClick={goToLogin}
            >
              Sign in
            </Button>
          </>
        )}
      </div>
    </header>
  );
}
