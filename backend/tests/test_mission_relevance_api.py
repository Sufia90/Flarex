import pytest
from fastapi.testclient import TestClient

from app.api.routes.mission_relevance import get_service as get_mission_service
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment, ExperimentalConditions, Finding
from app.schemas.hardware import Hardware, HardwareType
from app.schemas.relationship import ExperimentHardwareRelationship
from app.services.mission_relevance_service import MissionRelevanceService
from main import app


def _conditions(gravity="microgravity"):
    return ExperimentalConditions(
        fuel_material="methanol",
        oxygen_concentration=21.0,
        oxygen_unit="%",
        gravity_condition=gravity,
    )


def _experiment(experiment_id, name, missions=None, note=None, conditions=None, findings=None, source_ids=None):
    return Experiment(
        id=experiment_id,
        name=name,
        mission_applicability=missions or [],
        transferability_note=note,
        conditions=conditions,
        findings=findings or [],
        source_ids=source_ids or [],
    )


def _hardware(hardware_id, name):
    return Hardware(
        id=hardware_id,
        name=name,
        hardware_type=HardwareType.FACILITY,
        source_ids=["src-hw-001"],
    )


@pytest.fixture
def client(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    rel_repo = RelationshipRepository(data_dir=tmp_path / "relationships")
    exp_repo.create(_experiment("exp-iss", "Synthetic ISS Test", ["ISS"], "Applies to ISS fire safety.", _conditions(), [Finding(id="f-001", experiment_id="exp-iss", title="Synthetic finding")], ["src-001"]))
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["Moon"], "May transfer to lunar gravity.", _conditions()))
    exp_repo.create(_experiment("exp-mars", "Synthetic Mars Test", ["Mars"], None, _conditions()))
    exp_repo.create(_experiment("exp-unsup", "Synthetic Unsupported Test", [], None, _conditions()))
    exp_repo.create(_experiment("exp-earth", "Synthetic Earth Test", [], None, _conditions(gravity="earth gravity")))
    exp_repo.create(_experiment("exp-002", "Synthetic Thin Test"))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    hw_repo.create(_hardware("hw-empty", "Synthetic Empty"))
    rel_repo.create(ExperimentHardwareRelationship(id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", relationship_type="used_in"))
    service = MissionRelevanceService(experiment_repository=exp_repo, hardware_repository=hw_repo, relationship_repository=rel_repo)
    app.dependency_overrides[get_mission_service] = lambda: service
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


def test_experiment_iss_200(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-iss", params={"mission": "ISS"})
    assert response.status_code == 200
    data = response.json()
    assert data["mission"] == "ISS"
    assert data["relevance_level"] == "documented"
    assert data["subject_id"] == "exp-iss"
    assert data["methodology"]


def test_experiment_moon_200(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-001", params={"mission": "Moon"})
    assert response.status_code == 200
    data = response.json()
    assert data["mission"] == "Moon"
    assert data["relevance_level"] == "documented"


def test_experiment_mars_potential_200(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-mars", params={"mission": "Mars"})
    assert response.status_code == 200
    assert response.json()["relevance_level"] == "potential"


def test_experiment_unsupported_200(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-unsup", params={"mission": "Moon"})
    assert response.status_code == 200
    data = response.json()
    assert data["relevance_level"] == "unsupported"
    assert any("Microgravity findings do not automatically transfer" in item for item in data["transferability_limitations"])


def test_experiment_unknown_200(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-earth", params={"mission": "Mars"})
    assert response.status_code == 200
    assert response.json()["relevance_level"] == "unknown"


def test_experiment_insufficient_200(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-002", params={"mission": "Moon"})
    assert response.status_code == 200
    assert response.json()["relevance_level"] == "insufficient_evidence"


def test_hardware_derived_200(client):
    response = client.get("/api/v1/mission-relevance/hardware/hw-cir", params={"mission": "Moon"})
    assert response.status_code == 200
    data = response.json()
    assert data["subject_type"] == "hardware"
    assert data["relevance_level"] == "documented"
    assert data["derived_from_experiment_ids"] == ["exp-001"]


def test_hardware_no_links_200(client):
    response = client.get("/api/v1/mission-relevance/hardware/hw-empty", params={"mission": "Moon"})
    assert response.status_code == 200
    assert response.json()["relevance_level"] == "insufficient_evidence"


def test_missing_experiment_404(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-nope", params={"mission": "Moon"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_missing_hardware_404(client):
    response = client.get("/api/v1/mission-relevance/hardware/hw-nope", params={"mission": "Moon"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Hardware not found"


def test_invalid_mission_400(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-001", params={"mission": "Jupiter"})
    assert response.status_code == 400


def test_missing_mission_param_422(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-001")
    assert response.status_code == 422


def test_no_score_in_response(client):
    response = client.get("/api/v1/mission-relevance/experiments/exp-iss", params={"mission": "ISS"})
    assert response.status_code == 200
    assert not any("score" in key for key in response.json().keys())


def test_previous_modules_still_work(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    experiments = client.get("/api/v1/experiments")
    assert experiments.status_code == 200
    assert experiments.json()["total"] == 0
    hardware = client.get("/api/v1/hardware")
    assert hardware.status_code == 200
    assert hardware.json()["total"] == 0
