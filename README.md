# NASA Combustion Research Explorer

Explore · Compare · Understand · Apply

A dashboard-first research platform for NASA microgravity combustion investigations. Built for the NASA Space Apps Challenge 2026.

## Links

- **Live app:** https://flarex-neon.vercel.app/
- **GitHub:** https://github.com/Sufia90/Flarex
- **240-second video (YouTube):** https://youtu.be/uBNQT_M7zMw
- **Backend:** https://flarex-backend-c59g.onrender.com

## Team

**Team Solo Explorer, Cumilla, Bangladesh**

| Member | Role | University or organisation |
| --- | --- | --- |
| Sufia Akter | Team Leader and Lead Developer | International Islamic University Chittagong |
| Sadia Farjana Anika | Designer | International Islamic University Chittagong |
| Tonusree Devi Tuli | Researcher | International Islamic University Chittagong |
| Humaira Jannat | Data scientist | International Islamic University Chittagong |
| Md. Asif Wadud | Presenter / storyteller | Premier University Chittagong |

## What this project does

- Discover NASA combustion investigations (Overview, Experiment Explorer)
- Compare experiments and measurements with evidence (Compare & Rank)
- Assess mission relevance for ISS, Moon, and Mars with qualitative levels only, never numeric scores
- Learn fire prevention, detection, and suppression from documented evidence (Fire Safety Insights)
- Search records with deterministic keyword retrieval and ask the Research Assistant, which answers only from retrieved evidence and never invents answers

## Project structure

- backend: Python FastAPI backend (app/, main.py, requirements.txt, tests/)
- frontend: React + TypeScript + Vite frontend (src/, scripts/, dist/)
- data: research data in JSON and CSV, one folder per record type (experiments, hardware, relationships, sources, raw, processed, comparisons, rankings)
- media: experiment images, diagrams, and videos
- ai: future research retrieval and ML work
- docs: API inventory (docs/api/), data dictionary and import guide (docs/data-dictionary/), architecture, sources
- scripts: helper scripts, including the import validation CLI (scripts/validate_import.py)
- tests: backend tests live in backend/tests/; frontend tests live beside their source files

## Status

Modules 01-10 are complete and verified (2026-11-12): backend 388 tests pass, frontend 41 tests pass, API check 18/18, live CRUD check 25/25 against a temporary isolated backend. OpenAPI has 29 paths.

Real NASA data is now loaded and live: 10 experiments from NASA Physical Sciences Informatics (PSI): BASS, BASS-II, FLEX, SAFFIRE-I, SAFFIRE-II, SAFFIRE-III, SAME, SAME-R, SPICE, and ACME CFI-G.

- FLEX is fully confirmed against its source.
- The other experiments are marked partially documented, where checking against the cited NASA sources is not yet complete.
- Missing values are kept as missing. No fabricated NASA data is in the production data folders.
- BASS and BASS-II airflow is recorded as up to 40 cm/s.

The app is publicly deployed: frontend on Vercel and backend on Render. The Hardware section was removed from the frontend on 2026-11-13.

## Backend setup

From the project root, in a terminal:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend runs at http://127.0.0.1:8000. Health check: http://127.0.0.1:8000/api/health. Interactive API docs (Swagger UI): http://127.0.0.1:8000/docs. OpenAPI JSON: http://127.0.0.1:8000/openapi.json. API inventory: docs/api/api-inventory.md.

Note: pip install may fail building pyyaml on Windows (Microsoft Visual C++ 14.0 required). The project works with plain uvicorn, without the [standard] extra.

Run the backend tests (from backend/, with the venv active):

```
pytest
```

## Frontend setup

From the project root, in a terminal:

```
npm --prefix=frontend install
npm --prefix=frontend run dev
```

The frontend runs at http://localhost:5173. It talks to the backend at http://127.0.0.1:8000 (see frontend/.env.example: VITE_API_BASE_URL, VITE_API_PREFIX, VITE_API_TIMEOUT_MS).

Run the frontend tests, the production build, and the API check:

```
npm --prefix=frontend run test
npm --prefix=frontend run build
node frontend/scripts/verify-api.mjs
```

The API check needs the backend running. The CRUD check (frontend/scripts/verify-crud.mjs) must only run against a temporary backend on another port with an isolated data directory, never against the real backend or real data folders.

## Data organisation

- Real research records live only in data/<type>/ as JSON or CSV (experiments, hardware, relationships, sources).
- data/raw/ holds unprocessed source files; data/processed/ holds cleaned files; data/comparisons/ and data/rankings/ hold no stored results (comparisons and rankings are computed on demand).
- Test fixtures live only in backend/tests/fixtures/, and only when a test genuinely needs them.
- Synthetic records live only inside test files, clearly labelled synthetic.
- Media lives only in media/<type>/.
- Import reports go wherever --report writes them, never into data/.

## Adding real NASA data

Validate a file BEFORE it enters data/. From the project root, with the backend venv active:

```
python scripts/validate_import.py research/flex_experiments.json --type experiment
python scripts/validate_import.py research/flex_sources.json --type source --sources research/flex_sources.json --report research/flex_report.json
```

The script only validates. It never writes to data/, never overwrites, never deletes. A file with a failed report is not placed into data/. See docs/data-dictionary/import-guide.md for the full guide, required fields per record type, and the rules (missing values are never zero, numeric measurements must have a unit, measurement kind stays as written: measured, derived, or interpreted).

## Source verification workflow

- Every new source starts as unverified, which means not yet reviewed.
- A human reviewer checks the actual source (report, paper, dataset, or page) and then sets the status explicitly: confirmed (verified), partially_documented (partially verified), or verification_failed (reviewed and failed). Use POST /api/v1/sources/{id}/verification or update the record.
- A source record existing never verifies a finding or measurement. Findings and measurements keep their own verification status, independent of any source's status.
- A URL or NASA report ID existing does not verify a claim.

## Scientific limitations

- This is a research prototype, not a fire predictor. It does not predict fires, simulate combustion, or automate emergency decisions.
- Microgravity evidence is never automatically Moon or Mars evidence. Transferability must be documented per record.
- Potential applications are not proven results. They need further validation.
- Rankings use only documented criteria (experiments by documentation completeness, experiments by measurement coverage). There are no weights, no combined scores, and no best or safest ranking.
- The Research Assistant has no AI provider configured. It answers only from retrieved evidence and refuses to invent answers.
- Missing values are never shown as zero. Unknown is never shown as unsupported. Potential is never shown as documented. Derived or interpreted values are never shown as measured.

## Configuration

- Backend settings live in backend/.env (copy backend/.env.example). The root .env.example is a short summary; the backend one is authoritative.
- CORS allows only the local development origins (http://localhost:5173 and http://127.0.0.1:5173) unless CORS_ORIGINS is set in backend/.env (JSON array).
- Never commit real API keys, credentials, or .env files. See .gitignore.

## Notes

- No fake NASA data is included. Demo data, when added later, will be marked DEMO DATA.
- Real NASA data is loaded as described in Status above, after validation and source checking.
