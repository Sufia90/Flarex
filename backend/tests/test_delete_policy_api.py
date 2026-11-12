import pytest
from fastapi.testclient import TestClient
from main import app
from app.api.routes.experiments import get_service as get_experiment_service
from app.api.routes.hardware import get_service as get_hardware_service
from app.api.routes.relationships import get_service as get_relationship_service
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment
from app.schemas.hardware import Hardware, HardwareType
from app.services.experiment_service import ExperimentService
from app.services.hardware_service import HardwareService
from app.services.relationship_service import RelationshipService


def _relationship_payload(relationship_id="rel-001", experiment_id="exp-001", hardware_id="hw-cir"):
    return {
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


@pytest.fixture
def client(tmp_path):
    experiments_dir = tmp_path / "experiments"
    hardware_dir = tmp_path / "hardware"
    relationships_dir = tmp_path / "relationships"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    hardware_dir.mkdir(parents=True, exist_ok=True)
    relationships_dir.mkdir(parents=True, exist_ok=True)
    experiment_repository = ExperimentRepository(data_dir=experiments_dir)
    hardware_repository = HardwareRepository(data_dir=hardware_dir)
    relationship_repository = RelationshipRepository(data_dir=relationships_dir)
    experiment_repository.create(Experiment(id="exp-001", name="Synthetic FLEX Test"))
    hardware_repository.create(Hardware(id="hw-cir", name="Synthetic CIR", hardware_type=HardwareType.FACILITY))
    hardware_repository.create(Hardware(id="hw-msg", name="Synthetic MSG", hardware_type=HardwareType.FACILITY))
    experiment_service = ExperimentService(repository=experiment_repository, relationship_repository=relationship_repository)
    hardware_service = HardwareService(repository=hardware_repository, relationship_repository=relationship_repository)
    relationship_service = RelationshipService(repository=relationship_repository, experiment_repository=experiment_repository, hardware_repository=hardware_repository)
    app.dependency_overrides[get_experiment_service] = lambda: experiment_service
    app.dependency_overrides[get_hardware_service] = lambda: hardware_service
    app.dependency_overrides[get_relationship_service] = lambda: relationship_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_delete_experiment_blocked_when_relationship_exists(client):
    assert client.post("/api/v1/relationships", json=_relationship_payload()).status_code == 201
    response = client.delete("/api/v1/experiments/exp-001")
    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot delete experiment because relationships exist"
    assert client.get("/api/v1/experiments/exp-001").status_code == 200


def test_delete_experiment_allowed_after_relationship_deleted(client):
    assert client.post("/api/v1/relationships", json=_relationship_payload()).status_code == 201
    assert client.delete("/api/v1/experiments/exp-001").status_code == 409
    assert client.delete("/api/v1/relationships/rel-001").status_code == 200
    response = client.delete("/api/v1/experiments/exp-001")
    assert response.status_code == 200
    assert response.json()["deleted_id"] == "exp-001"
    assert client.get("/api/v1/experiments/exp-001").status_code == 404


def test_delete_experiment_allowed_when_no_relationship(client):
    response = client.delete("/api/v1/experiments/exp-001")
    assert response.status_code == 200
    assert client.get("/api/v1/experiments/exp-001").status_code == 404


def test_delete_hardware_blocked_when_relationship_exists(client):
    assert client.post("/api/v1/relationships", json=_relationship_payload()).status_code == 201
    response = client.delete("/api/v1/hardware/hw-cir")
    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot delete hardware because relationships exist"
    assert client.get("/api/v1/hardware/hw-cir").status_code == 200


def test_delete_hardware_allowed_after_relationship_deleted(client):
    assert client.post("/api/v1/relationships", json=_relationship_payload()).status_code == 201
    assert client.delete("/api/v1/hardware/hw-cir").status_code == 409
    assert client.delete("/api/v1/relationships/rel-001").status_code == 200
    response = client.delete("/api/v1/hardware/hw-cir")
    assert response.status_code == 200
    assert response.json()["deleted_id"] == "hw-cir"
    assert client.get("/api/v1/hardware/hw-cir").status_code == 404


def test_delete_hardware_allowed_when_no_relationship(client):
    response = client.delete("/api/v1/hardware/hw-msg")
    assert response.status_code == 200
    assert client.get("/api/v1/hardware/hw-msg").status_code == 404


def test_delete_missing_parent_still_404(client):
    assert client.delete("/api/v1/experiments/exp-no-such").status_code == 404
    assert client.delete("/api/v1/hardware/hw-no-such").status_code == 404
