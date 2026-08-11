# Game Theory Laboratory — Frontend

React + TypeScript interface for the university Game Theory project **Prisoner's
Dilemma Strategy Tournament**, based on Philip D. Straffin's *Game Theory and
Strategy*.

The application lets you read the theory, edit a payoff matrix and see it
analysed, simulate matches between strategies, run Axelrod-style tournaments,
and run a classroom experiment with real participants.

> **This is the frontend only.** It contains no game-theory logic. Every
> equilibrium, dominance result, payoff, score and ranking is computed by the
> FastAPI backend and displayed here. That separation keeps one source of truth
> for anything that ends up in a report.

---

## Technology stack

| Concern | Choice |
|---|---|
| Framework | React 19 (function components, hooks) |
| Language | TypeScript (strict) |
| Build tool | Vite 8 |
| Styling | Tailwind CSS 4 |
| Routing | React Router 7 |
| HTTP | Axios |
| Charts | Recharts 3 |
| Icons | Lucide React |
| Forms | React Hook Form + Zod |

---

## Installation

```bash
npm install
```

## Environment variables

Copy the example file and adjust if your backend runs elsewhere:

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Base URL of the FastAPI backend, including the `/api/v1` prefix |
| `VITE_USE_MOCK_API` | `false` | `true` serves fixture data from the local mock adapter and shows a Demo Mode banner |

No URL is hard-coded in any component — everything goes through
`src/api/client.ts`.

## Development

```bash
npm run dev
```

Opens on <http://localhost:5173>, which is the origin the backend's CORS
configuration allows by default.

## Production build

```bash
npm run build
npm run preview
```

`npm run build` runs `tsc -b` first, so a type error fails the build.

---

## Connecting to the FastAPI backend

1. Start the backend from the repository root:

   ```bash
   uvicorn app.main:app --reload
   ```

2. Confirm it is reachable — <http://localhost:8000/docs> should show Swagger.

3. Make sure `frontend/.env` has:

   ```
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   VITE_USE_MOCK_API=false
   ```

4. Restart `npm run dev` after changing `.env` — Vite only reads it at startup.

5. Backend CORS must allow the dev origin. In the backend's `.env`:

   ```
   CORS_ORIGINS=http://localhost:5173
   ```

If the backend is not running, every page still renders and shows a clear
"Unable to connect to the backend" state with a retry button rather than a
blank screen.

### Demo Mode

Setting `VITE_USE_MOCK_API=true` installs an Axios adapter that replays
fixtures from `src/api/mock/`, and an amber **Demo Mode** banner appears under
the top bar. It is for developing the UI without a backend.

The mock replays recorded examples; it does not simulate anything, because the
frontend deliberately holds no game-theory logic. Any request it has no fixture
for returns an explicit error telling you to connect the real backend — it never
invents a result silently.

---

## Folder structure

```
src/
├── api/                    # the only place Axios is used
│   ├── client.ts           # base URL, JWT header, envelope unwrapping, ApiError
│   ├── authApi.ts
│   ├── gameTheoryApi.ts
│   ├── payoffMatrixApi.ts
│   ├── strategyApi.ts
│   ├── matchApi.ts
│   ├── tournamentApi.ts
│   ├── experimentApi.ts
│   ├── surveyApi.ts
│   ├── statisticsApi.ts
│   └── mock/               # Demo Mode fixtures and adapter (dev only)
├── components/
│   ├── layout/             # AppLayout, Sidebar, Topbar, PageHeader, navigation
│   ├── common/             # Card, Button, Badge, DataTable, Dialog, Tabs, Field,
│   │                       # StatCard, Skeleton, Spinner, EmptyState, ErrorState,
│   │                       # InfoTooltip
│   ├── charts/             # ChartFrame + Recharts wrappers
│   └── game/               # ActionBadge, PayoffMatrixGrid, RoundHistoryTable,
│                           # ConceptCard
├── features/
│   ├── auth/               # LoginDialog, RequireRole
│   ├── gameTheory/         # AnalysisPanels (conditions, dominance, Nash, Pareto)
│   ├── experiment/         # HiddenChoicePanel
│   └── tournament/         # StatusBadge
├── pages/                  # one file per route
├── hooks/                  # useApiResource, useApiAction + feature hooks
├── context/                # AuthContext, ToastContext
├── routes/                 # AppRoutes (lazy-loaded pages)
├── types/                  # every backend schema, mirrored
└── utils/                  # cn, format, download, game labels and colours
```

---

## Routes

| Path | Page | What it does |
|---|---|---|
| `/` | → `/dashboard` | Redirect |
| `/dashboard` | DashboardPage | Totals, cooperation rates, ranking charts, recent activity |
| `/game-theory` | GameTheoryPage | Eight tabbed explanations, verified against a live analysis |
| `/payoff-matrix` | PayoffMatrixPage | Editable 2×2 matrix, re-analysed by the backend on change |
| `/match-simulator` | MatchSimulatorPage | Run one iterated match, with charts and full round history |
| `/strategies` | StrategiesPage | The six strategies with rules, behaviour and examples |
| `/tournament` | TournamentPage | Configure and create a round robin; list existing ones |
| `/tournament/:id` | TournamentDetailPage | Run it, ranking table, four charts, head-to-head matrix |
| `/tournament/:id/matches` | TournamentMatchesPage | Every match, with a round-by-round drill-down |
| `/experiments` | ExperimentsPage | Create and list classroom experiments |
| `/experiments/:id` | ExperimentDetailPage | Participants, pairing, session control |
| `/experiments/:id/play` | ExperimentPlayPage | Hidden simultaneous choices, reveal, next round |
| `/experiments/:id/results` | ExperimentResultsPage | Rates, Nash comparison, four charts |
| `/statistics` | StatisticsPage | Descriptive statistics for tournaments and experiments |
| `/trust-survey` | TrustSurveyPage | Record 1–5 answers; expected vs actual cooperation |
| `/about` | AboutPage | Sources, chapters used, project structure |
| `*` | NotFoundPage | Unknown route |

---

## Backend API contract

All paths are relative to `VITE_API_BASE_URL`.

**Auth** — `POST /auth/register`, `POST /auth/login`, `GET /auth/me`

**Game theory** — `POST /game-theory/analyze`

**Payoff matrices** — `GET|POST /payoff-matrices`, `GET|PUT|DELETE /payoff-matrices/{id}`

**Strategies** — `GET /strategies`, `GET /strategies/{id}`

**Matches** — `POST /matches/simulate`, `GET /matches/{id}`

**Tournaments** — `GET|POST /tournaments`, `GET /tournaments/{id}`,
`POST /tournaments/{id}/run`, `GET /tournaments/{id}/results`,
`GET /tournaments/{id}/matches`, `GET /tournaments/{id}/matches/{match_id}`,
`GET /tournaments/{id}/statistics`, `GET /tournaments/{id}/export/results.csv`

**Experiments** — `GET|POST /experiments`, `GET /experiments/{id}`,
`POST /experiments/{id}/participants`,
`DELETE /experiments/{id}/participants/{participant_id}`,
`POST /experiments/{id}/start`, `POST /experiments/{id}/rounds`,
`GET /experiments/{id}/results`, `GET /experiments/{id}/statistics`,
`GET /experiments/{id}/export/rounds.csv`

**Surveys** — `POST /surveys/trust`, `GET /experiments/{id}/surveys/trust`,
`GET /experiments/{id}/surveys/trust/statistics`

### Response envelope

Success:

```json
{ "success": true, "data": {}, "message": null }
```

Error:

```json
{ "success": false, "data": null, "message": "Validation failed", "errors": [] }
```

`src/api/client.ts` unwraps `data` on success and converts any failure into a
single `ApiError` shape with a readable message. Statuses 400, 401, 403, 404,
409, 422 and 500 each get their own wording, and a dropped connection is
reported separately from a rejected request.

### Example request

```http
POST /api/v1/matches/simulate
Content-Type: application/json

{
  "strategy_a_id": "TIT_FOR_TAT",
  "strategy_b_id": "ALWAYS_DEFECT",
  "rounds": 10,
  "seed": 42
}
```

Response (abridged):

```json
{
  "success": true,
  "message": null,
  "data": {
    "strategy_a_id": "TIT_FOR_TAT",
    "strategy_b_id": "ALWAYS_DEFECT",
    "rounds_played": 10,
    "player_a": { "total_payoff": 9, "cooperation_rate": 0.1 },
    "player_b": { "total_payoff": 14, "cooperation_rate": 0.0 },
    "winner": "ALWAYS_DEFECT",
    "outcome_counts": { "CC": 0, "CD": 1, "DC": 0, "DD": 9 },
    "rounds": [
      {
        "round_number": 1,
        "player_a_action": "COOPERATE",
        "player_b_action": "DEFECT",
        "player_a_payoff": 0,
        "player_b_payoff": 5,
        "outcome": "CD"
      }
    ]
  }
}
```

---

## Authentication

JWT, held in `AuthContext` and persisted to `localStorage`. The token is
attached by an Axios request interceptor.

Roles are `ADMIN`, `TEACHER` and `STUDENT`. Authentication does **not** block
navigation: every page stays readable while signed out so the interface can be
developed and demonstrated without a session. Instead, `RequireRole` wraps the
individual write actions — creating tournaments, running them, managing
participants — which the backend would reject anyway.

---

## Accessibility

- Semantic landmarks, a skip link, and labelled form controls throughout
- Visible focus rings; dialogs trap and restore focus and close on Escape
- Tabs implement the WAI-ARIA pattern with arrow-key navigation
- Cooperate/Defect is **never** signalled by colour alone — every instance
  carries an icon and a text label
- Loading, empty and error states are announced with `role="status"` /
  `role="alert"`
- `prefers-reduced-motion` disables animation

---

## Commands

```bash
npm install        # install dependencies
npm run dev        # development server on :5173
npm run build      # type check, then production build to dist/
npm run preview    # serve the production build locally
npx tsc -b --noEmit  # type check only
```
