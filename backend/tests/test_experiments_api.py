import pytest
from fastapi.testclient import TestClient
from main import app
from app.api.routes.experiments import get_service
from app.repositories.experiment_repository import ExperimentRepository
from app.services.experiment_service import ExperimentService


@pytest.fixture
def client(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    service = ExperimentService(repository=repository)
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def _payload(experiment_id="exp-001", name="Synthetic FLEX test", **overrides):
    payload = {
        "id": experiment_id,
        "name": name,
        "research_category": "droplet combustion",
        "fuel_material": "methanol",
        "hardware_ids": ["MDCA"],
        "mission_applicability": ["ISS"],
        "fire_safety_relevance": ["prevention"],
    }
    payload.update(overrides)
    return payload


def test_create_valid_experiment(client):
    response = client.post("/api/v1/experiments", json=_payload())
    assert response.status_code == 201
    assert response.json()["id"] == "exp-001"
    assert response.json()["name"] == "Synthetic FLEX test"


def test_get_experiment_by_id(client):
    client.post("/api/v1/experiments", json=_payload())
    response = client.get("/api/v1/experiments/exp-001")
    assert response.status_code == 200
    assert response.json()["id"] == "exp-001"


def test_get_all_experiments(client):
    client.post("/api/v1/experiments", json=_payload("exp-001", "Synthetic FLEX test"))
    client.post("/api/v1/experiments", json=_payload("exp-002", "Synthetic ACME test"))
    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2


def test_update_experiment(client):
    client.post("/api/v1/experiments", json=_payload("exp-001", "Synthetic FLEX test"))
    client.post("/api/v1/experiments", json=_payload("exp-002", "Synthetic ACME test"))
    response = client.put(
        "/api/v1/experiments/exp-001",
        json=_payload("exp-001", "Updated synthetic test", fuel_material="heptane"),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated synthetic test"
    assert response.json()["fuel_material"] == "heptane"
    other = client.get("/api/v1/experiments/exp-002")
    assert other.json()["name"] == "Synthetic ACME test"


def test_delete_experiment(client):
    client.post("/api/v1/experiments", json=_payload("exp-001", "Synthetic FLEX test"))
    client.post("/api/v1/experiments", json=_payload("exp-002", "Synthetic ACME test"))
    response = client.delete("/api/v1/experiments/exp-001")
    assert response.status_code == 200
    assert response.json()["deleted_id"] == "exp-001"
    assert client.get("/api/v1/experiments/exp-001").status_code == 404
    listed = client.get("/api/v1/experiments")
    assert listed.json()["total"] == 1


def test_search_experiments(client):
    client.post("/api/v1/experiments", json=_payload("exp-001", "Synthetic FLEX test"))
    client.post(
        "/api/v1/experiments",
        json=_payload("exp-002", "Synthetic ACME test", research_category="flame spread", fuel_material="heptane", hardware_ids=["CIR"]),
    )
    response = client.get("/api/v1/experiments/search", params={"query": "heptane"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == "exp-002"
    response = client.get("/api/v1/experiments/search", params={"research_category": "droplet combustion"})
    assert response.json()["total"] == 1


def test_filter_by_supported_fields(client):
    client.post("/api/v1/experiments", json=_payload("exp-001", "Synthetic FLEX test"))
    client.post(
        "/api/v1/experiments",
        json=_payload(
            "exp-002",
            "Synthetic ACME test",
            research_category="flame spread",
            fuel_material="heptane",
            hardware_ids=["CIR"],
            mission_applicability=["Moon"],
            fire_safety_relevance=["detection"],
            conditions={"gravity_condition": "lunar"},
        ),
    )
    client.post(
        "/api/v1/experiments",
        json=_payload(
            "exp-003",
            "Synthetic FLEX-2 test",
            mission_applicability=["Mars"],
            fire_safety_relevance=["suppression"],
            conditions={"gravity_condition": "microgravity"},
        ),
    )
    assert client.get("/api/v1/experiments/search", params={"fuel_material": "methanol"}).json()["total"] == 2
    assert client.get("/api/v1/experiments/search", params={"mission_applicability": "Moon"}).json()["total"] == 1
    assert client.get("/api/v1/experiments/search", params={"fire_safety_relevance": "suppression"}).json()["total"] == 1
    assert client.get("/api/v1/experiments/search", params={"gravity_condition": "microgravity"}).json()["total"] == 1
    assert client.get("/api/v1/experiments/search", params={"hardware_id": "CIR"}).json()["total"] == 1


def test_pagination_works(client):
    client.post("/api/v1/experiments", json=_payload("exp-001", "Synthetic FLEX test"))
    client.post("/api/v1/experiments", json=_payload("exp-002", "Synthetic ACME test"))
    client.post("/api/v1/experiments", json=_payload("exp-003", "Synthetic FLEX-2 test"))
    first = client.get("/api/v1/experiments", params={"page": 1, "page_size": 2})
    assert first.status_code == 200
    assert first.json()["total"] == 3
    assert first.json()["total_pages"] == 2
    assert len(first.json()["items"]) == 2
    second = client.get("/api/v1/experiments", params={"page": 2, "page_size": 2})
    assert len(second.json()["items"]) == 1


def test_empty_dataset_returns_empty_response(client):
    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["total_pages"] == 0
    assert response.json()["items"] == []
    searched = client.get("/api/v1/experiments/search", params={"query": "flex"})
    assert searched.json()["total"] == 0
    assert searched.json()["items"] == []


def test_duplicate_experiment_id_is_rejected(client):
    client.post("/api/v1/experiments", json=_payload())
    response = client.post("/api/v1/experiments", json=_payload())
    assert response.status_code == 409


def test_invalid_experiment_payload_is_rejected(client):
    response = client.post("/api/v1/experiments", json={"id": "exp-bad"})
    assert response.status_code == 422
    bad_kind = _payload()
    bad_kind["measurements"] = [
        {
            "id": "m-001",
            "experiment_id": "exp-001",
            "parameter_name": "oxygen concentration",
            "value": 20.0,
            "unit": "%",
            "measurement_kind": "estimated",
        }
    ]
    response = client.post("/api/v1/experiments", json=bad_kind)
    assert response.status_code == 422


def test_nonexistent_experiment_returns_404(client):
    assert client.get("/api/v1/experiments/no-such").status_code == 404
    assert client.put("/api/v1/experiments/no-such", json=_payload("no-such", "Synthetic test")).status_code == 404
    assert client.delete("/api/v1/experiments/no-such").status_code == 404


def test_invalid_pagination_values_are_rejected(client):
    assert client.get("/api/v1/experiments", params={"page": 0}).status_code == 422
    assert client.get("/api/v1/experiments", params={"page_size": 0}).status_code == 422
    assert client.get("/api/v1/experiments", params={"page_size": 101}).status_code == 422


def test_module02_fields_remain_supported(client):
    payload = _payload()
    payload["transferability_note"] = "Synthetic note for testing only"
    payload["measurements"] = [
        {
            "id": "m-001",
            "experiment_id": "exp-001",
            "parameter_name": "oxygen concentration",
            "value": 20.0,
            "unit": "%",
            "measurement_kind": "derived",
        }
    ]
    response = client.post("/api/v1/experiments", json=payload)
    assert response.status_code == 201
    assert response.json()["mission_applicability"] == ["ISS"]
    assert response.json()["transferability_note"] == "Synthetic note for testing only"
    assert response.json()["fire_safety_relevance"] == ["prevention"]
    assert response.json()["measurements"][0]["measurement_kind"] == "derived"


def test_missing_values_remain_distinct_from_zero(client):
    zero_payload = _payload()
    zero_payload["measurements"] = [
        {
            "id": "m-001",
            "experiment_id": "exp-001",
            "parameter_name": "oxygen concentration",
            "value": 0.0,
            "unit": "%",
        }
    ]
    response = client.post("/api/v1/experiments", json=zero_payload)
    assert response.status_code == 201
    assert response.json()["measurements"][0]["value"] == 0.0
    assert response.json()["measurements"][0]["value"] is not None
    missing_payload = _payload("exp-002", "Synthetic ACME test")
    missing_payload["measurements"] = [
        {
            "id": "m-002",
            "experiment_id": "exp-002",
            "parameter_name": "oxygen concentration",
            "value": None,
            "unit": "%",
        }
    ]
    response = client.post("/api/v1/experiments", json=missing_payload)
    assert response.json()["measurements"][0]["value"] is None


def test_update_does_not_change_other_records(client):
    client.post("/api/v1/experiments", json=_payload("exp-001", "Synthetic FLEX test"))
    client.post("/api/v1/experiments", json=_payload("exp-002", "Synthetic ACME test", fuel_material="heptane"))
    client.put("/api/v1/experiments/exp-001", json=_payload("exp-001", "Updated synthetic test"))
    other = client.get("/api/v1/experiments/exp-002")
    assert other.json()["name"] == "Synthetic ACME test"
    assert other.json()["fuel_material"] == "heptane"
    listed = client.get("/api/v1/experiments")
    assert listed.json()["total"] == 2
