import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";

interface Breadcrumb {
  label: string;
  to?: string;
}

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  breadcrumbs?: Breadcrumb[];
  icon?: ReactNode;
}

export function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  icon,
}: PageHeaderProps) {
  return (
    <div className="mb-6">
      {breadcrumbs && breadcrumbs.length > 0 ? (
        <nav aria-label="Breadcrumb" className="mb-2">
          <ol className="flex flex-wrap items-center gap-1 text-xs text-slate-500">
            {breadcrumbs.map((crumb, index) => (
              <li key={`${crumb.label}-${index}`} className="flex items-center gap-1">
                {index > 0 ? <ChevronRight className="h-3 w-3" aria-hidden /> : null}
                {crumb.to ? (
                  <Link to={crumb.to} className="transition-colors hover:text-indigo-600">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-lab-700">{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      ) : null}

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {icon ? (
            <span className="rounded-lg bg-indigo-50 p-2 text-indigo-600" aria-hidden>
              {icon}
            </span>
          ) : null}
          <div>
            <h1 className="text-xl font-semibold text-lab-950 sm:text-2xl">{title}</h1>
            {description ? (
              <p className="mt-1 max-w-3xl text-sm text-slate-600">{description}</p>
            ) : null}
          </div>
        </div>

        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
    </div>
  );
}
