import pytest
from fastapi.testclient import TestClient

from app.api.routes.rankings import get_service as get_ranking_service
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment, ExperimentalConditions, Finding, Measurement
from app.schemas.hardware import Hardware, HardwareType
from app.schemas.relationship import ExperimentHardwareRelationship
from app.services.ranking_service import RankingService
from main import app


def _measurement(measurement_id, experiment_id):
    return Measurement(
        id=measurement_id,
        experiment_id=experiment_id,
        parameter_name="flame_temperature",
        value=1000.0,
        unit="K",
        measurement_kind="measured",
        measurement_method="thermocouple",
        source_id="src-m-001",
    )


def _experiment(experiment_id, name, full=False, measurements=None):
    if full:
        return Experiment(
            id=experiment_id,
            name=name,
            description="A description.",
            scientific_objective="An objective.",
            research_category="flammability",
            conditions=ExperimentalConditions(fuel_material="methanol", oxygen_concentration=21.0, oxygen_unit="%", gravity_condition="microgravity"),
            measurements=[_measurement("m-001", experiment_id)],
            findings=[Finding(id="f-001", experiment_id=experiment_id, title="Synthetic finding")],
            limitations=["Some limitations."],
            source_ids=["src-001"],
        )
    return Experiment(id=experiment_id, name=name, measurements=measurements or [])


def _hardware(hardware_id, name):
    return Hardware(
        id=hardware_id,
        name=name,
        hardware_type=HardwareType.FACILITY,
        source_ids=["src-hw-001"],
    )


def _relationship(relationship_id, experiment_id, hardware_id):
    return ExperimentHardwareRelationship(
        id=relationship_id,
        experiment_id=experiment_id,
        hardware_id=hardware_id,
        relationship_type="used_in",
    )


@pytest.fixture
def client(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    rel_repo = RelationshipRepository(data_dir=tmp_path / "relationships")
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", full=True))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test"))
    exp_repo.create(_experiment("exp-003", "Synthetic SLICE Test", measurements=[_measurement("m-002", "exp-003")]))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    hw_repo.create(_hardware("hw-msg", "Synthetic MSG"))
    hw_repo.create(_hardware("hw-empty", "Synthetic Empty"))
    rel_repo.create(_relationship("rel-001", "exp-001", "hw-cir"))
    rel_repo.create(_relationship("rel-002", "exp-002", "hw-cir"))
    rel_repo.create(_relationship("rel-003", "exp-001", "hw-msg"))
    service = RankingService(experiment_repository=exp_repo, hardware_repository=hw_repo, relationship_repository=rel_repo)
    app.dependency_overrides[get_ranking_service] = lambda: service
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


def _item(data, item_id):
    for item in data["items"]:
        if item["item_id"] == item_id:
            return item
    raise AssertionError(f"item {item_id} not found")


def test_rank_hardware_associations_200(client):
    response = client.post("/api/v1/rankings", json={"criterion": "hardware_experiment_associations"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ranked"
    assert data["criterion"] == "hardware_experiment_associations"
    assert _item(data, "hw-cir")["rank"] == 1
    assert _item(data, "hw-cir")["metric_value"] == 2
    assert _item(data, "hw-msg")["rank"] == 2
    assert _item(data, "hw-empty")["rank"] is None
    assert data["methodology"]
    assert data["limitations"]


def test_rank_documentation_completeness_200(client):
    response = client.post("/api/v1/rankings", json={"criterion": "experiment_documentation_completeness"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ranked"
    assert data["metric_max"] == 9
    assert _item(data, "exp-001")["rank"] == 1
    assert _item(data, "exp-001")["metric_value"] == 9
    assert _item(data, "exp-002")["metric_value"] == 1


def test_rank_measurement_coverage_200(client):
    response = client.post("/api/v1/rankings", json={"criterion": "experiment_measurement_coverage", "item_ids": ["exp-001", "exp-003"]})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ranked"
    assert _item(data, "exp-001")["rank"] == 1
    assert _item(data, "exp-001")["metric_value"] == 1
    assert _item(data, "exp-003")["rank"] == 1
    assert _item(data, "exp-003")["metric_value"] == 1


def test_insufficient_evidence_200(client):
    response = client.post("/api/v1/rankings", json={"criterion": "hardware_experiment_associations", "item_ids": ["hw-cir"]})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient_evidence"
    assert all(item["rank"] is None for item in data["items"])


def test_invalid_criterion_422(client):
    response = client.post("/api/v1/rankings", json={"criterion": "best_hardware"})
    assert response.status_code == 422


def test_missing_experiment_404(client):
    response = client.post("/api/v1/rankings", json={"criterion": "experiment_measurement_coverage", "item_ids": ["exp-001", "exp-nope"]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_missing_hardware_404(client):
    response = client.post("/api/v1/rankings", json={"criterion": "hardware_experiment_associations", "item_ids": ["hw-nope"]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Hardware not found"


def test_duplicate_item_ids_400(client):
    response = client.post("/api/v1/rankings", json={"criterion": "experiment_measurement_coverage", "item_ids": ["exp-001", "exp-001"]})
    assert response.status_code == 400


def test_limit_validation_422(client):
    response = client.post("/api/v1/rankings", json={"criterion": "hardware_experiment_associations", "limit": 0})
    assert response.status_code == 422
    response = client.post("/api/v1/rankings", json={"criterion": "hardware_experiment_associations", "limit": 51})
    assert response.status_code == 422


def test_limit_applied_200(client):
    response = client.post("/api/v1/rankings", json={"criterion": "hardware_experiment_associations", "limit": 1})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert len(data["eligible_item_ids"]) == 3


def test_previous_modules_still_work(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    experiments = client.get("/api/v1/experiments")
    assert experiments.status_code == 200
    assert experiments.json()["total"] == 0
    hardware = client.get("/api/v1/hardware")
    assert hardware.status_code == 200
    assert hardware.json()["total"] == 0
