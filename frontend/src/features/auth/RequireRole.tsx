import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { Lock } from "lucide-react";
import { EmptyState } from "@/components/common/EmptyState";
import { useAuth } from "@/context/AuthContext";
import type { UserRole } from "@/types";

interface RequireRoleProps {
  roles: UserRole[];
  children: ReactNode;
  /** Shown instead of the children when the role check fails. */
  fallback?: ReactNode;
}

/**
 * Gate for write actions.
 *
 * Deliberately not a route guard: every page stays readable while signed out,
 * so the UI can be explored and demonstrated without a backend session. Only
 * the controls that would fail server-side are hidden.
 */
export function RequireRole({ roles, children, fallback }: RequireRoleProps) {
  const { hasRole, isAuthenticated } = useAuth();
  const location = useLocation();

  if (hasRole(...roles)) return <>{children}</>;
  if (fallback !== undefined) return <>{fallback}</>;

  return (
    <EmptyState
      icon={<Lock className="h-6 w-6" />}
      title={isAuthenticated ? "Not permitted for your role" : "Sign in to continue"}
      description={
        isAuthenticated
          ? `This action needs one of these roles: ${roles.join(", ")}.`
          : `Sign in with a ${roles.join(" or ")} account to use this. Everything on this page can still be read while signed out.`
      }
      action={
        isAuthenticated ? undefined : (
          <Link
            to="/login"
            state={{ from: location.pathname + location.search }}
            className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-700"
          >
            Sign in
          </Link>
        )
      }
    />
  );
}
