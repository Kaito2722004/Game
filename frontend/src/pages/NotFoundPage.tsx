import { Link } from "react-router-dom";
import { Compass } from "lucide-react";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";

export function NotFoundPage() {
  return (
    <Card>
      <EmptyState
        icon={<Compass className="h-6 w-6" />}
        title="Page not found"
        description="That route does not exist in this application."
        action={
          <Link
            to="/dashboard"
            className="text-sm font-medium text-violet-400 hover:text-violet-300"
          >
            Back to the dashboard
          </Link>
        }
      />
    </Card>
  );
}
