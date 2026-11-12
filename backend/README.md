# NASA Combustion Research Explorer - Backend

Python FastAPI backend for the NASA Combustion Research Explorer. JSON file storage, no database. The full project guide is the root README.md; this file covers the backend only.

## Start

From this folder, with the virtual environment active:

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

The backend runs at http://127.0.0.1:8000. Health check: http://127.0.0.1:8000/api/health. Interactive API docs (Swagger UI): http://127.0.0.1:8000/docs. OpenAPI JSON: http://127.0.0.1:8000/openapi.json.

Note: pip install may fail building pyyaml on Windows (Microsoft Visual C++ 14.0 required). The project works with plain uvicorn, without the [standard] extra.

## Tests

From this folder, with the venv active:

pytest

388 tests pass (2026-11-12). One harmless StarletteDeprecationWarning about TestClient appears in every run.

## Layout

- main.py: app factory, CORS, health endpoint, all routers under /api
- app/core/: config.py (settings from .env, CORS origins, data and media paths) and logging_config.py
- app/schemas/: Pydantic models (common, experiment, hardware, relationship incl. Source, comparison, ranking, mission_relevance, fire_safety, retrieval, response)
- app/repositories/: JSON file repositories (experiment, hardware, relationship, source) with invalid-record preservation and atomic writes
- app/services/: business logic (experiment, hardware, relationship, source, comparison, ranking, mission_relevance, fire_safety, validation)
- app/api/routes/: one router per resource (experiments, hardware, relationships, sources, comparisons, rankings, mission-relevance, fire-safety)
- app/ai/: retrieval (deterministic keyword search, not semantic AI), assistant (no-provider stub), evaluation, config
- tests/: pytest tests; tests/fixtures/ holds fixtures only when a test genuinely needs them

## API

29 paths, 41 operations (2026-11-12). Full CRUD for experiments, hardware, relationships, and sources; comparisons and rankings are POST only; mission relevance and fire safety are GET only; source verification is POST /api/v1/sources/{id}/verification. Retrieval and the Research Assistant have no HTTP endpoints (service-only by design). See docs/api/api-inventory.md for the full inventory, and docs/data-dictionary/import-guide.md for the import validation CLI.

## Rules

- Routes take their service via Depends(get_service), never by calling get_service() directly, or test dependency overrides silently stop working.
- A source record existing never verifies a finding or measurement; verification statuses are independent.
- Missing values are never zero; measurement kind stays measured, derived, or interpreted as written.
- Never invent NASA data. Tests use tmp_path only and never write to the real data folders.
