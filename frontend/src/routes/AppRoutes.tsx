import { Suspense, lazy } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoadingBlock } from "@/components/common/Spinner";
import { useAuth } from "@/context/AuthContext";

/**
 * Where the application opens.
 *
 * Signed out, it opens on the sign-in page. Signed in, it goes straight to
 * the dashboard, so a returning user is not asked to sign in again.
 *
 * The wait on `initialising` matters: while the stored token is being checked
 * the user is not yet known to be authenticated, and redirecting early would
 * bounce a signed-in user to the login page on every refresh.
 */
function RootRedirect() {
  const { isAuthenticated, initialising } = useAuth();

  if (initialising) return <LoadingBlock label="Starting" />;
  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
}

/**
 * Every route in the application.
 *
 * Pages are readable without a session; role checks guard individual write
 * actions instead, so the interface can be explored and demonstrated freely.
 *
 * Pages are lazily imported so that the charting library is only downloaded
 * when a route that actually plots something is opened.
 */

const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage })),
);
const GameTheoryPage = lazy(() =>
  import("@/pages/GameTheoryPage").then((m) => ({ default: m.GameTheoryPage })),
);
const PayoffMatrixPage = lazy(() =>
  import("@/pages/PayoffMatrixPage").then((m) => ({ default: m.PayoffMatrixPage })),
);
const StrategiesPage = lazy(() =>
  import("@/pages/StrategiesPage").then((m) => ({ default: m.StrategiesPage })),
);
const MatchSimulatorPage = lazy(() =>
  import("@/pages/MatchSimulatorPage").then((m) => ({ default: m.MatchSimulatorPage })),
);
const TournamentPage = lazy(() =>
  import("@/pages/TournamentPage").then((m) => ({ default: m.TournamentPage })),
);
const TournamentDetailPage = lazy(() =>
  import("@/pages/TournamentDetailPage").then((m) => ({ default: m.TournamentDetailPage })),
);
const TournamentMatchesPage = lazy(() =>
  import("@/pages/TournamentMatchesPage").then((m) => ({ default: m.TournamentMatchesPage })),
);
const ExperimentsPage = lazy(() =>
  import("@/pages/ExperimentsPage").then((m) => ({ default: m.ExperimentsPage })),
);
const ExperimentDetailPage = lazy(() =>
  import("@/pages/ExperimentDetailPage").then((m) => ({ default: m.ExperimentDetailPage })),
);
const ExperimentPlayPage = lazy(() =>
  import("@/pages/ExperimentPlayPage").then((m) => ({ default: m.ExperimentPlayPage })),
);
const ExperimentResultsPage = lazy(() =>
  import("@/pages/ExperimentResultsPage").then((m) => ({ default: m.ExperimentResultsPage })),
);
const HistoryPage = lazy(() =>
  import("@/pages/HistoryPage").then((m) => ({ default: m.HistoryPage })),
);
const StatisticsPage = lazy(() =>
  import("@/pages/StatisticsPage").then((m) => ({ default: m.StatisticsPage })),
);
const TrustSurveyPage = lazy(() =>
  import("@/pages/TrustSurveyPage").then((m) => ({ default: m.TrustSurveyPage })),
);
const AboutPage = lazy(() =>
  import("@/pages/AboutPage").then((m) => ({ default: m.AboutPage })),
);
const NotFoundPage = lazy(() =>
  import("@/pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })),
);
const LoginPage = lazy(() =>
  import("@/pages/LoginPage").then((m) => ({ default: m.LoginPage })),
);

export function AppRoutes() {
  return (
    <Routes>
      {/* Sign-in sits outside the app shell: no sidebar, full screen. */}
      <Route
        path="login"
        element={
          <Suspense fallback={<LoadingBlock label="Loading sign in" />}>
            <LoginPage />
          </Suspense>
        }
      />

      {/* The landing decision, outside the shell so no sidebar flashes first. */}
      <Route index element={<RootRedirect />} />

      <Route element={<AppLayout />}>
        <Route
          element={
            <Suspense fallback={<LoadingBlock label="Loading page" />}>
              <Outlet />
            </Suspense>
          }
        >
          <Route path="dashboard" element={<DashboardPage />} />

          <Route path="game-theory" element={<GameTheoryPage />} />
          <Route path="payoff-matrix" element={<PayoffMatrixPage />} />
          <Route path="strategies" element={<StrategiesPage />} />

          <Route path="match-simulator" element={<MatchSimulatorPage />} />

          <Route path="tournament" element={<TournamentPage />} />
          <Route path="tournament/:id" element={<TournamentDetailPage />} />
          <Route path="tournament/:id/matches" element={<TournamentMatchesPage />} />

          <Route path="experiments" element={<ExperimentsPage />} />
          <Route path="experiments/:id" element={<ExperimentDetailPage />} />
          <Route path="experiments/:id/play" element={<ExperimentPlayPage />} />
          <Route path="experiments/:id/results" element={<ExperimentResultsPage />} />

          <Route path="history" element={<HistoryPage />} />
          <Route path="statistics" element={<StatisticsPage />} />
          <Route path="trust-survey" element={<TrustSurveyPage />} />
          <Route path="about" element={<AboutPage />} />

          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
