import pytest
from fastapi.testclient import TestClient

from app.api.routes.fire_safety import get_service as get_fire_safety_service
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment, Finding
from app.schemas.hardware import Hardware, HardwareType
from app.schemas.relationship import ExperimentHardwareRelationship
from app.services.fire_safety_service import FireSafetyService
from main import app


def _finding(finding_id, experiment_id, categories, observation):
    return Finding(
        id=finding_id,
        experiment_id=experiment_id,
        title="Synthetic finding",
        observation=observation,
        fire_safety_relevance=categories,
        source_id="src-f-001",
    )


def _experiment(experiment_id, name, categories=None, findings=None, source_ids=None, missions=None, hardware_ids=None):
    return Experiment(
        id=experiment_id,
        name=name,
        fire_safety_relevance=categories or [],
        findings=findings or [],
        source_ids=source_ids or [],
        mission_applicability=missions or [],
        hardware_ids=hardware_ids or [],
    )


def _hardware(hardware_id, name):
    return Hardware(
        id=hardware_id,
        name=name,
        hardware_type=HardwareType.FACILITY,
        source_ids=["src-hw-001"],
    )


def _make_client(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    rel_repo = RelationshipRepository(data_dir=tmp_path / "relationships")
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention", "detection"], [_finding("f-001", "exp-001", ["prevention"], "Methanol flame behaviour was observed."), _finding("f-002", "exp-001", ["detection"], "Smoke was observed by the sensor.")], ["src-001"], ["Moon"], ["hw-cir"]))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test", ["suppression"], [], [], ["ISS"]))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    rel_repo.create(ExperimentHardwareRelationship(id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", relationship_type="used_in"))
    service = FireSafetyService(experiment_repository=exp_repo, hardware_repository=hw_repo, relationship_repository=rel_repo)
    app.dependency_overrides[get_fire_safety_service] = lambda: service
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client(tmp_path):
    yield from _make_client(tmp_path)


@pytest.fixture
def empty_client(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    rel_repo = RelationshipRepository(data_dir=tmp_path / "relationships")
    service = FireSafetyService(experiment_repository=exp_repo, hardware_repository=hw_repo, relationship_repository=rel_repo)
    app.dependency_overrides[get_fire_safety_service] = lambda: service
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


def test_list_insights_200(client):
    response = client.get("/api/v1/fire-safety/insights")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert all("category" in item and "evidence_status" in item for item in data["items"])


def test_filter_category_200(client):
    response = client.get("/api/v1/fire-safety/insights", params={"category": "prevention"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "prevention"


def test_filter_evidence_status_200(client):
    response = client.get("/api/v1/fire-safety/insights", params={"evidence_status": "insufficient_evidence"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "suppression"


def test_filter_experiment_200(client):
    response = client.get("/api/v1/fire-safety/insights", params={"experiment_id": "exp-001"})
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_filter_mission_200(client):
    response = client.get("/api/v1/fire-safety/insights", params={"mission": "Moon"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["experiment_id"] == "exp-001" for item in data["items"])


def test_invalid_mission_400(client):
    response = client.get("/api/v1/fire-safety/insights", params={"mission": "Jupiter"})
    assert response.status_code == 400


def test_invalid_experiment_filter_404(client):
    response = client.get("/api/v1/fire-safety/insights", params={"experiment_id": "exp-nope"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_prevention_200(client):
    response = client.get("/api/v1/fire-safety/prevention")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "prevention"
    assert data["items"][0]["evidence_status"] == "documented"


def test_detection_200(client):
    response = client.get("/api/v1/fire-safety/detection")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "detection"


def test_suppression_200(client):
    response = client.get("/api/v1/fire-safety/suppression")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["evidence_status"] == "insufficient_evidence"


def test_summary_200(client):
    response = client.get("/api/v1/fire-safety/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_experiments"] == 2
    assert data["total_insights"] == 3
    assert data["prevention_count"] == 1
    assert data["detection_count"] == 1
    assert data["suppression_count"] == 1
    assert data["documented_count"] == 2
    assert data["insufficient_evidence_count"] == 1
    assert data["experiments_with_evidence"] == 2
    assert data["experiments_without_evidence"] == 0


def test_experiment_insights_200(client):
    response = client.get("/api/v1/fire-safety/experiments/exp-001")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_experiment_insights_filter_200(client):
    response = client.get("/api/v1/fire-safety/experiments/exp-001", params={"category": "detection"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "detection"


def test_experiment_not_found_404(client):
    response = client.get("/api/v1/fire-safety/experiments/exp-nope")
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_hardware_insights_200(client):
    response = client.get("/api/v1/fire-safety/hardware/hw-cir")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["derived"] is True for item in data)
    assert all(item["hardware_ids"] == ["hw-cir"] for item in data)


def test_hardware_not_found_404(client):
    response = client.get("/api/v1/fire-safety/hardware/hw-nope")
    assert response.status_code == 404
    assert response.json()["detail"] == "Hardware not found"


def test_pagination_200(client):
    first = client.get("/api/v1/fire-safety/insights", params={"page": 1, "page_size": 1})
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["total"] == 3
    assert first_data["total_pages"] == 3
    assert len(first_data["items"]) == 1
    second = client.get("/api/v1/fire-safety/insights", params={"page": 2, "page_size": 1})
    assert second.status_code == 200
    assert second.json()["items"][0]["insight_id"] != first_data["items"][0]["insight_id"]


def test_pagination_validation_422(client):
    response = client.get("/api/v1/fire-safety/insights", params={"page_size": 0})
    assert response.status_code == 422


def test_empty_dataset_200(empty_client):
    insights = empty_client.get("/api/v1/fire-safety/insights")
    assert insights.status_code == 200
    assert insights.json()["total"] == 0
    summary = empty_client.get("/api/v1/fire-safety/summary")
    assert summary.status_code == 200
    data = summary.json()
    assert data["total_experiments"] == 0
    assert data["total_insights"] == 0
    assert data["prevention_count"] == 0
    assert data["detection_count"] == 0
    assert data["suppression_count"] == 0


def test_previous_modules_still_work(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    experiments = client.get("/api/v1/experiments")
    assert experiments.status_code == 200
    assert experiments.json()["total"] == 0
    hardware = client.get("/api/v1/hardware")
    assert hardware.status_code == 200
    assert hardware.json()["total"] == 0
