import pytest
from fastapi.testclient import TestClient
from main import app
from app.api.routes.relationships import get_service
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment
from app.schemas.hardware import Hardware, HardwareType
from app.services.relationship_service import RelationshipService


def _relationship_payload(relationship_id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", **overrides):
    payload = {
        "id": relationship_id,
        "experiment_id": experiment_id,
        "hardware_id": hardware_id,
        "relationship_type": "used_in",
        "role": "Synthetic role for testing only",
        "evidence": "Synthetic evidence for testing only",
        "source_id": "src-001",
        "verification_status": "unverified",
        "notes": "Synthetic note for testing only",
    }
    payload.update(overrides)
    return payload


def _build_client(base):
    experiments_dir = base / "experiments"
    hardware_dir = base / "hardware"
    relationships_dir = base / "relationships"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    hardware_dir.mkdir(parents=True, exist_ok=True)
    relationships_dir.mkdir(parents=True, exist_ok=True)
    experiment_repository = ExperimentRepository(data_dir=experiments_dir)
    hardware_repository = HardwareRepository(data_dir=hardware_dir)
    relationship_repository = RelationshipRepository(data_dir=relationships_dir)
    experiment_repository.create(Experiment(id="exp-001", name="Synthetic FLEX Test"))
    experiment_repository.create(Experiment(id="exp-002", name="Synthetic ACME Test"))
    hardware_repository.create(Hardware(id="hw-cir", name="Synthetic CIR", hardware_type=HardwareType.FACILITY))
    hardware_repository.create(Hardware(id="hw-msg", name="Synthetic MSG", hardware_type=HardwareType.FACILITY))
    service = RelationshipService(
        repository=relationship_repository,
        experiment_repository=experiment_repository,
        hardware_repository=hardware_repository,
    )
    app.dependency_overrides[get_service] = lambda: service
    return TestClient(app)


@pytest.fixture
def client(tmp_path):
    test_client = _build_client(tmp_path)
    yield test_client
    app.dependency_overrides.clear()


def test_create_relationship(client):
    response = client.post("/api/v1/relationships", json=_relationship_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "rel-001"
    assert body["experiment_id"] == "exp-001"
    assert body["hardware_id"] == "hw-cir"
    assert body["relationship_type"] == "used_in"
    assert body["role"] == "Synthetic role for testing only"


def test_list_relationships(client):
    client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-001", "hw-cir"))
    client.post("/api/v1/relationships", json=_relationship_payload("rel-002", "exp-002", "hw-msg"))
    response = client.get("/api/v1/relationships")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["total_pages"] == 1
    assert len(body["items"]) == 2


def test_get_relationship_by_id(client):
    client.post("/api/v1/relationships", json=_relationship_payload())
    response = client.get("/api/v1/relationships/rel-001")
    assert response.status_code == 200
    assert response.json()["hardware_id"] == "hw-cir"


def test_update_relationship(client):
    client.post("/api/v1/relationships", json=_relationship_payload())
    response = client.put("/api/v1/relationships/rel-001", json=_relationship_payload("rel-999", "exp-001", "hw-cir", role="Updated synthetic role"))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "rel-001"
    assert body["role"] == "Updated synthetic role"


def test_delete_relationship(client):
    client.post("/api/v1/relationships", json=_relationship_payload())
    response = client.delete("/api/v1/relationships/rel-001")
    assert response.status_code == 200
    assert response.json()["deleted_id"] == "rel-001"
    assert client.get("/api/v1/relationships/rel-001").status_code == 404


def test_search_relationships(client):
    client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-001", "hw-cir"))
    client.post("/api/v1/relationships", json=_relationship_payload("rel-002", "exp-001", "hw-msg", relationship_type="housed_in", role="Synthetic housing role"))
    response = client.get("/api/v1/relationships/search", params={"query": "housing"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    response = client.get("/api/v1/relationships/search", params={"relationship_type": "used_in"})
    assert response.json()["total"] == 1


def test_filter_by_experiment_id(client):
    client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-001", "hw-cir"))
    client.post("/api/v1/relationships", json=_relationship_payload("rel-002", "exp-002", "hw-msg"))
    response = client.get("/api/v1/relationships", params={"experiment_id": "exp-001"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == "rel-001"


def test_filter_by_hardware_id(client):
    client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-001", "hw-cir"))
    client.post("/api/v1/relationships", json=_relationship_payload("rel-002", "exp-002", "hw-cir", relationship_type="housed_in"))
    response = client.get("/api/v1/relationships", params={"hardware_id": "hw-cir"})
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_get_by_experiment(client):
    client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-001", "hw-cir"))
    client.post("/api/v1/relationships", json=_relationship_payload("rel-002", "exp-001", "hw-msg", relationship_type="housed_in"))
    client.post("/api/v1/relationships", json=_relationship_payload("rel-003", "exp-002", "hw-cir", relationship_type="supports"))
    response = client.get("/api/v1/relationships/by-experiment/exp-001")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    response = client.get("/api/v1/relationships/by-experiment/exp-002")
    assert response.json()["total"] == 1


def test_get_by_hardware(client):
    client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-001", "hw-cir"))
    client.post("/api/v1/relationships", json=_relationship_payload("rel-002", "exp-002", "hw-cir", relationship_type="housed_in"))
    response = client.get("/api/v1/relationships/by-hardware/hw-cir")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    response = client.get("/api/v1/relationships/by-hardware/hw-msg")
    assert response.json()["total"] == 0


def test_create_with_invalid_experiment_reference(client):
    response = client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-no-such", "hw-cir"))
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_create_with_invalid_hardware_reference(client):
    response = client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-001", "hw-no-such"))
    assert response.status_code == 404
    assert response.json()["detail"] == "Hardware not found"


def test_create_duplicate_relationship_id(client):
    client.post("/api/v1/relationships", json=_relationship_payload())
    response = client.post("/api/v1/relationships", json=_relationship_payload("rel-001", "exp-002", "hw-msg"))
    assert response.status_code == 409


def test_create_duplicate_relationship_link(client):
    client.post("/api/v1/relationships", json=_relationship_payload())
    response = client.post("/api/v1/relationships", json=_relationship_payload("rel-002", "exp-001", "hw-cir"))
    assert response.status_code == 409


def test_create_invalid_payload(client):
    response = client.post("/api/v1/relationships", json=_relationship_payload(relationship_type="teleported"))
    assert response.status_code == 422


def test_missing_relationship_returns_404(client):
    assert client.get("/api/v1/relationships/rel-no-such").status_code == 404
    assert client.put("/api/v1/relationships/rel-no-such", json=_relationship_payload("rel-no-such", "exp-001", "hw-cir")).status_code == 404
    assert client.delete("/api/v1/relationships/rel-no-such").status_code == 404


def test_missing_experiment_returns_404(client):
    response = client.get("/api/v1/relationships/by-experiment/exp-no-such")
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_missing_hardware_returns_404(client):
    response = client.get("/api/v1/relationships/by-hardware/hw-no-such")
    assert response.status_code == 404
    assert response.json()["detail"] == "Hardware not found"


def test_invalid_pagination_returns_422(client):
    assert client.get("/api/v1/relationships", params={"page": 0}).status_code == 422
    assert client.get("/api/v1/relationships", params={"page_size": 0}).status_code == 422
    assert client.get("/api/v1/relationships", params={"page_size": 101}).status_code == 422


def test_empty_dataset(tmp_path):
    empty_client = _build_client(tmp_path / "empty")
    try:
        response = empty_client.get("/api/v1/relationships")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["total_pages"] == 0
        assert body["items"] == []
        response = empty_client.get("/api/v1/relationships/by-experiment/exp-001")
        assert response.status_code == 200
        assert response.json()["total"] == 0
    finally:
        app.dependency_overrides.clear()


def test_previous_modules_still_work(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    response = client.get("/api/v1/hardware")
    assert response.status_code == 200
    assert response.json()["total"] == 0
