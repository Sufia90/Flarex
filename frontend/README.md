# NASA Combustion Research Explorer - Frontend

React + TypeScript + Vite frontend for the NASA Combustion Research Explorer. It talks to the FastAPI backend in `..\backend` through a central API client. Six dashboard sections (Overview, Experiment Explorer, Hardware Explorer, Compare & Rank, Fire Safety Insights, Mission Relevance) plus a Research Assistant route that never pretends to be an operational AI chatbot.

## Tech stack

- React 19 + TypeScript + Vite 8
- Tailwind CSS 4
- React Router 8 (routing; import from 'react-router', never 'react-router-dom')
- TanStack Query 5 (data fetching, caching, refetching)
- Fetch-based API client (no axios)
- Three.js + React Three Fiber + Drei (illustrative 3D hardware views)
- Recharts (category bar charts, lazy-loaded)
- Vitest + React Testing Library + jsdom (tests)

## Prerequisites

- Node.js 20 or later
- The backend running (see below)

## Start the backend

From `C:\FLAREX\backend`, in a terminal with the virtual environment active:

uvicorn main:app --reload --port 8000

The backend runs at http://127.0.0.1:8000. Health check: http://127.0.0.1:8000/api/health.

## Start the frontend

From the project root:

npm --prefix=frontend install
npm --prefix=frontend run dev

The frontend runs at http://localhost:5173.

## Configuration

Copy `frontend/.env.example` to `frontend/.env` and adjust if needed:

VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_API_PREFIX=/api
VITE_API_TIMEOUT_MS=10000

Never put secrets in frontend env files. The API base URL and prefix are the only settings; feature files must not hardcode URLs.

## API client

- `src/api/config.ts`: base URL, API prefix, and timeout from env (defaults above).
- `src/api/errors.ts`: ApiError with kind 'network' | 'timeout' | 'http' | 'malformed', plus isApiError and apiErrorMessage.
- `src/api/client.ts`: apiClient with get/post/put/delete, AbortController timeout, and FastAPI {detail} error parsing.
- `src/api/endpoints.ts`: every backend endpoint in one place (29 paths, including /v1/sources and /v1/sources/{id}/verification). Feature code imports paths from here, never writes URLs inline.

## Types

`src/types/` mirrors the backend Pydantic schemas exactly: common, experiment, hardware, relationship (including Source), comparison, ranking, mission-relevance, fire-safety, plus index.ts. Rules: backend responses always include every field, so TS properties are required keys with `| null` where the backend allows None; nothing is optional-keyed. Measurement value is `boolean | number | string | null`. VerificationStatus is 'confirmed' | 'partially_documented' | 'unverified' | 'verification_failed'. BaseRecord created_at and updated_at are `string | null`. Filter objects passed to withQuery must be `type` aliases, not `interface`.

## Services and hooks

One service module and one hooks module per feature, in `src/services/` and `src/hooks/`:

- health, experiments, hardware, relationships, comparisons, rankings, mission-relevance, fire-safety, sources
- Services use apiClient and endpoints; search filter types are `type` aliases.
- Hooks use TanStack Query v5. Queries take (page, pageSize) or an id; mutations invalidate their feature key on success (update and verification also invalidate the detail key).
- Sources: listSources, searchSources, getSource, createSource, updateSource, deleteSource, setSourceVerification; hooks useSources, useSource, useSearchSources, useCreateSource, useUpdateSource, useDeleteSource, useSetSourceVerification.

## Pages and routes

`src/app/router.tsx` (createBrowserRouter, named page exports only) with `src/app/providers.tsx` (QueryClient, retry false, staleTime 30000) and `src/layouts/AppLayout.tsx` (header, nav, Outlet). Routes: / (Overview), /experiments, /hardware, /compare, /fire-safety, /mission-relevance, /research-assistant, * (NotFound). Cross-section links use query params: /experiments?id=, /hardware?id=, /mission-relevance?subject=&id=&mission=, /fire-safety?experiment=&category=&hardware=.

## Components

- `src/components/feedback/`: LoadingState, ErrorState, EmptyState, NotFoundState, ConnectionUnavailable. An API failure is never shown as an empty dataset.
- `src/components/common/`: EvidenceStatusBadge (text label always shown, never color alone; includes verification_failed in red, comparable tones), StatCard.
- `src/components/charts/CategoryBarChart.tsx`: Recharts bar chart; empty data shows "No data to chart yet." It is lazy-loaded in OverviewPage and FireSafetyPage, so Recharts leaves the main bundle.
- `src/features/`: OverviewStats, HardwareViewport, HardwareInfoPanel, ExperimentFilters, ExperimentDetail, ComparisonPanel, RankingPanel, InsightCard, RelevancePanel.

## 3D hardware views

`src/features/hardware/HardwareViewport.tsx` renders an illustrative 3D model per hardware record (facility, apparatus, or MSG glovebox), labelled "Illustrative model — not to scale. This is not an exact NASA engineering model." No verified NASA 3D assets exist in the repository, so no real dimensions, internal structures, or component names are shown; the whole record is selectable, never fake sub-components. OrbitControls comes from Drei (its only use here). WebGL unavailable shows a clean non-3D fallback. The viewport is lazy-loaded, so Three.js loads only on the Hardware page. The chunk is large (935.61 kB) because three.js core alone is 647.36 kB; that is inherent to Three.js, not a Drei problem, and the warning is never hidden by raising limits.

## Tests

Vitest + React Testing Library + jsdom. Run from the project root:

npm --prefix=frontend run test

41 tests in 11 files (2026-11-12): components, features, services, and hooks, all with mocked fetch or mocked hooks. No real server is needed. New API service or hook tests belong beside their source file (for example src/services/sources.test.ts and src/hooks/useSources.test.tsx). Test fixtures live only in backend/tests/fixtures/ and only when a test genuinely needs them; frontend tests use inline mock data.

## Check scripts

From the project root, with the backend running:

node frontend/scripts/verify-api.mjs

18 read-only checks (health, lists, searches, fire-safety, comparison POST, ranking POST, mission relevance, invalid endpoint, CORS preflight). The CRUD check (frontend/scripts/verify-crud.mjs) runs 25 create/read/update/delete checks and must only run against a temporary backend on another port with an isolated data directory, never against the real backend or real data folders.

## Production build and bundle

npm --prefix=frontend run build

tsc -b must be clean, then Vite builds. Sizes (2026-11-12): main JS 408.26 kB (gzip 121.50 kB), lazy chart chunk 368.11 kB, lazy HardwareViewport chunk 935.61 kB, CSS 14.20 kB. The 500 kB chunk warning for the 3D chunk is expected and never hidden. Bundle analysis: install rollup-plugin-visualizer (already a devDependency), then run the build with ANALYZE=true (PowerShell: $env:ANALYZE="true"; npm --prefix=frontend run build) and open frontend/dist/stats.html. @types/node is a devDependency because vite.config.ts reads process.env.ANALYZE.

## Scientific data rules

- Missing is never zero. Unknown is never unsupported. Potential is never documented. Derived or interpreted is never measured.
- Incompatible units are never compared; different units return not_comparable.
- Microgravity is never auto-presented as Moon or Mars evidence.
- Rankings use only the three documented backend criteria; the frontend adds no ranking algorithm, weights, or combined score, and never says which experiment is best or safest overall.
- Summary counts are never shown as percentages unless the denominator is clear.
- Zero counts are shown as 0 with an honest explanation, never hidden. Backend availability is not NASA data availability.
- No fabricated NASA records in the UI. Empty states say so plainly.

## Type sync guide

When a backend schema changes: paste the backend schema file, update the matching file in src/types/ (required vs optional, nullability, enums, nested and list structures, measurement value types), update the request and response types in the matching service, run the build and the tests, and update docs/api/api-inventory.md. Never invent a field name from memory.

## Adding a feature

1. Add the endpoint to src/api/endpoints.ts.
2. Add the type to src/types/ (and export it from index.ts).
3. Add the service in src/services/ (filter types as `type`).
4. Add the hook in src/hooks/ (invalidate the feature key on mutation success).
5. Add the feature component under src/features/<name>/ and wire it into a page.
6. Add tests beside the new files. Run the build and the tests.

## Troubleshooting

- Frontend cannot reach the backend: check the backend is running on http://127.0.0.1:8000, check frontend/.env values, and look for a CORS error (the backend allows only http://localhost:5173 and http://127.0.0.1:5173).
- "Cannot find module 'react-router-dom'": import routing APIs from 'react-router', never 'react-router-dom'.
- withQuery type error on a filter object: declare the filter as `type`, not `interface` (interfaces have no implicit index signature).
- Page import error "has no exported member": pages use named exports, never default exports (only App.tsx uses a default export).
- Build warning "INEFFECTIVE_DYNAMIC_IMPORT": a lazily imported module is also statically imported somewhere; make every import of it dynamic.
- Tests fail with stale DOM between files: src/test/setup.ts runs cleanup() after each test; keep it.
- THREE CJS deprecation warning and jsdom "getContext not implemented" notes in tests are harmless; the second is why the WebGL fallback tests work.
