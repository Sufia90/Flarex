# API Inventory

Source: the live OpenAPI schema (`app.openapi()`), checked 2026-11-12. **29 paths, 41 method operations.**

- Interactive docs: Swagger UI at `/docs`, OpenAPI JSON at `/openapi.json`.
- Base URL when the backend runs locally: `http://127.0.0.1:8000`.
- All resource routes live under `/api/v1/...`. Health is at `/api/health`.
- Error responses use the FastAPI envelope: `{"detail": "<message>"}`.
- List responses use the paginated envelope: `{"total", "page", "page_size", "total_pages", "items"}`.
- Retrieval (keyword search over records) and the Research Assistant have no HTTP endpoints. They are service-only by design: retrieval is deterministic substring matching, and the assistant is a no-provider stub that never invents answers. There is no AI provider endpoint.

## Health

| Method | Path | Purpose | Success | Errors |
| GET | /api/health | Backend status | 200 `HealthResponse` | - |

## Experiments — `/api/v1/experiments`

| Method | Path | Purpose | Success | Errors |
| POST | /api/v1/experiments | Create an experiment | 201 `Experiment` | 409 duplicate id, 422 invalid body |
| GET | /api/v1/experiments | List, paginated (`page`, `page_size` 1-100) | 200 `PaginatedExperimentList` | 422 bad pagination |
| GET | /api/v1/experiments/search | Search and filter (query, research_category, fuel_material, hardware_id, gravity_condition, mission_applicability, fire_safety_relevance, data_completeness) | 200 `PaginatedExperimentList` | 422 bad pagination |
| GET | /api/v1/experiments/{experiment_id} | Get one (id, investigation id, or acronym, case-insensitive) | 200 `Experiment` | 404 not found |
| PUT | /api/v1/experiments/{experiment_id} | Update (id is forced to the URL id) | 200 `Experiment` | 404 not found, 422 invalid body |
| DELETE | /api/v1/experiments/{experiment_id} | Delete | 200 `DeleteResponse` | 404 not found, 409 has relationships |

## Hardware — `/api/v1/hardware`

| Method | Path | Purpose | Success | Errors |
| POST | /api/v1/hardware | Create a hardware record | 201 `Hardware` | 409 duplicate id, 422 invalid body |
| GET | /api/v1/hardware | List, paginated | 200 `PaginatedHardwareList` | 422 bad pagination |
| GET | /api/v1/hardware/search | Search and filter (query, hardware_type, parent_hardware_id, facility_classification, supported_measurements, related_experiment_ids) | 200 `PaginatedHardwareList` | 422 bad pagination |
| GET | /api/v1/hardware/{hardware_id} | Get one (id or acronym, case-insensitive) | 200 `Hardware` | 404 not found |
| PUT | /api/v1/hardware/{hardware_id} | Update (id is forced to the URL id) | 200 `Hardware` | 404 not found, 422 invalid body |
| DELETE | /api/v1/hardware/{hardware_id} | Delete | 200 `DeleteResponse` | 404 not found, 409 has relationships |

## Relationships — `/api/v1/relationships`

| Method | Path | Purpose | Success | Errors |
| POST | /api/v1/relationships | Create a link | 201 `ExperimentHardwareRelationship` | 409 duplicate id, 409 duplicate link, 404 experiment or hardware not found, 422 invalid body |
| GET | /api/v1/relationships | List, paginated | 200 `PaginatedRelationshipList` | 422 bad pagination |
| GET | /api/v1/relationships/search | Search and filter (query, experiment_id, hardware_id, relationship_type, verification_status, role) | 200 `PaginatedRelationshipList` | 422 bad pagination |
| GET | /api/v1/relationships/by-experiment/{experiment_id} | Links for one experiment | 200 list | 404 experiment not found |
| GET | /api/v1/relationships/by-hardware/{hardware_id} | Links for one hardware record | 200 list | 404 hardware not found |
| GET | /api/v1/relationships/{relationship_id} | Get one | 200 `ExperimentHardwareRelationship` | 404 not found |
| PUT | /api/v1/relationships/{relationship_id} | Update (id is forced to the URL id) | 200 `ExperimentHardwareRelationship` | 404 not found, 422 invalid body |
| DELETE | /api/v1/relationships/{relationship_id} | Delete | 200 `DeleteResponse` | 404 not found |

## Sources — `/api/v1/sources` (new in Module 10)

| Method | Path | Purpose | Success | Errors |
| POST | /api/v1/sources | Create a source (starts `unverified`) | 201 `Source` | 409 duplicate id, 422 invalid body (missing title, bad doi or url) |
| GET | /api/v1/sources | List, paginated | 200 `PaginatedSourceList` | 422 bad pagination |
| GET | /api/v1/sources/search | Search and filter (query, source_type, verification_status, nasa_report_id, publisher) | 200 `PaginatedSourceList` | 422 bad pagination |
| GET | /api/v1/sources/{source_id} | Get one | 200 `Source` | 404 not found |
| PUT | /api/v1/sources/{source_id} | Update (id is forced to the URL id) | 200 `Source` | 404 not found, 422 invalid body |
| DELETE | /api/v1/sources/{source_id} | Delete | 200 `DeleteResponse` | 404 not found |
| POST | /api/v1/sources/{source_id}/verification | Set verification status (`confirmed`, `partially_documented`, `unverified`, `verification_failed`) | 200 `Source` | 404 not found, 400 invalid value, 422 invalid status |

## Comparisons — `/api/v1/comparisons`

| Method | Path | Purpose | Success | Errors |
| POST | /api/v1/comparisons/experiments | Compare 2-10 experiments | 200 `ExperimentComparison` | 404 experiment not found, 400 bad ids, 422 fewer than 2 or more than 10 ids |
| POST | /api/v1/comparisons/hardware | Compare 2-10 hardware records | 200 `HardwareComparison` | 404 hardware not found, 400 bad ids, 422 fewer than 2 or more than 10 ids |
| POST | /api/v1/comparisons/measurements | Compare 2-10 measurements | 200 `MeasurementComparison` | 404 measurement not found, 400 bad ids, 422 fewer than 2 or more than 10 ids |

No unit conversion. Different units return `not_comparable` with a reason. Results are computed on demand and never stored.

## Rankings — `/api/v1/rankings`

| Method | Path | Purpose | Success | Errors |
| POST | /api/v1/rankings | Rank by one criterion (`hardware_experiment_associations`, `experiment_documentation_completeness`, `experiment_measurement_coverage`) | 200 `RankingResult` | 404 record not found, 400 bad request, 422 invalid criterion |

Only 3 criteria. No weights, no combined score, no best or safest ranking. Insufficient evidence returns `insufficient_evidence` with ranks cleared.

## Mission relevance — `/api/v1/mission-relevance`

| Method | Path | Purpose | Success | Errors |
| GET | /api/v1/mission-relevance/experiments/{experiment_id}?mission= | Assess one experiment for ISS, Moon, or Mars | 200 `MissionRelevanceAssessment` | 404 not found, 400 bad mission |
| GET | /api/v1/mission-relevance/hardware/{hardware_id}?mission= | Assess one hardware record (derived from linked experiments) | 200 `MissionRelevanceAssessment` | 404 not found, 400 bad mission |

Qualitative levels only (`documented`, `potential`, `unsupported`, `unknown`, `insufficient_evidence`). No numeric score. Microgravity is never auto-valid for Moon or Mars.

## Fire safety — `/api/v1/fire-safety`

| Method | Path | Purpose | Success | Errors |
| GET | /api/v1/fire-safety/insights | List insights (filters: category, evidence_status, experiment_id, hardware_id, mission, page, page_size) | 200 `PaginatedFireSafetyInsightList` | 400 bad mission, 422 bad pagination |
| GET | /api/v1/fire-safety/prevention | Prevention insights, paginated | 200 `PaginatedFireSafetyInsightList` | 422 bad pagination |
| GET | /api/v1/fire-safety/detection | Detection insights, paginated | 200 `PaginatedFireSafetyInsightList` | 422 bad pagination |
| GET | /api/v1/fire-safety/suppression | Suppression insights, paginated | 200 `PaginatedFireSafetyInsightList` | 422 bad pagination |
| GET | /api/v1/fire-safety/summary | Counts by evidence status | 200 `FireSafetySummary` | - |
| GET | /api/v1/fire-safety/experiments/{experiment_id} | Insights for one experiment | 200 list | 404 not found |
| GET | /api/v1/fire-safety/hardware/{hardware_id} | Insights for one hardware record (derived) | 200 list | 404 not found |

Documented evidence, derived interpretation, and potential applications are kept in separate fields. A potential application is never presented as a proven result.

## Method coverage

- Full CRUD (POST, GET, PUT, DELETE) is covered by backend API tests for experiments, hardware, relationships, and sources.
- The read-only check script (`frontend/scripts/verify-api.mjs`) runs 18 checks against the running backend: health, list and search for experiments, hardware, and relationships, fire-safety insights, summary, prevention, detection, and suppression, a comparison POST (expects 404 on empty data), a ranking POST (expects 200 on empty data), mission relevance (expects 404 on empty data), an invalid endpoint (expects 404), and a CORS preflight (expects 200).
- PUT and DELETE are never run against the real data folders. They are verified only against a temporary backend with an isolated data directory, and the real data folders are checked unchanged afterwards.
