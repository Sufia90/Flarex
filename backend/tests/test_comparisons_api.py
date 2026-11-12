import pytest
from fastapi.testclient import TestClient

from app.api.routes.comparisons import get_service as get_comparison_service
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.schemas.experiment import Experiment, ExperimentalConditions, Measurement
from app.schemas.hardware import Hardware, HardwareType
from app.services.comparison_service import ComparisonService
from main import app


def _conditions(gravity="microgravity", oxygen=21.0):
    return ExperimentalConditions(
        fuel_material="methanol",
        oxygen_concentration=oxygen,
        oxygen_unit="%",
        oxygen_basis="mole",
        ambient_pressure=101.3,
        pressure_unit="kPa",
        temperature=25.0,
        temperature_unit="C",
        airflow_velocity=0.1,
        airflow_unit="m/s",
        gravity_condition=gravity,
        sample_geometry="droplet",
    )


def _measurement(measurement_id, experiment_id, value=1000.0, unit="K"):
    return Measurement(
        id=measurement_id,
        experiment_id=experiment_id,
        parameter_name="flame_temperature",
        value=value,
        unit=unit,
        measurement_kind="measured",
        measurement_method="thermocouple",
        sensor="TC-1",
        source_id="src-m-001",
    )


def _experiment(experiment_id, name, measurements=None, conditions=None):
    return Experiment(
        id=experiment_id,
        name=name,
        conditions=conditions,
        measurements=measurements or [],
        source_ids=["src-exp-001"],
    )


def _hardware(hardware_id, name, facility="rack", measurements=None):
    return Hardware(
        id=hardware_id,
        name=name,
        hardware_type=HardwareType.FACILITY,
        facility_classification=facility,
        purpose="Test rack",
        supported_measurements=measurements or [],
        related_experiment_ids=[],
        source_ids=["src-hw-001"],
    )


@pytest.fixture
def client(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", [_measurement("m-001", "exp-001")], _conditions()))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test", [_measurement("m-002", "exp-002")], _conditions()))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR", measurements=["temperature", "pressure"]))
    hw_repo.create(_hardware("hw-msg", "Synthetic MSG", facility="glovebox", measurements=["temperature", "imaging"]))
    service = ComparisonService(experiment_repository=exp_repo, hardware_repository=hw_repo)
    app.dependency_overrides[get_comparison_service] = lambda: service
    test_client = TestClient(app)
    try:
        yield test_client, exp_repo, hw_repo
    finally:
        app.dependency_overrides.clear()


def test_compare_experiments_200(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-001", "exp-002"]})
    assert response.status_code == 200
    data = response.json()
    assert data["comparison_id"] == "cmp-exp-exp-001-exp-002"
    assert data["experiment_ids"] == ["exp-001", "exp-002"]
    row = [item for item in data["parameters"] if item["parameter_name"] == "flame_temperature"][0]
    assert row["status"] == "comparable"
    assert data["methodology"]
    assert data["limitations"]


def test_compare_hardware_200(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/hardware", json={"hardware_ids": ["hw-cir", "hw-msg"]})
    assert response.status_code == 200
    data = response.json()
    assert data["same_hardware_type"] is True
    assert data["shared_measurements"] == ["temperature"]
    assert data["unique_measurements"]["hw-cir"] == ["pressure"]


def test_compare_measurements_200(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/measurements", json={"measurement_ids": ["m-001", "m-002"]})
    assert response.status_code == 200
    data = response.json()
    assert data["measurement_ids"] == ["m-001", "m-002"]
    row = [item for item in data["parameters"] if item["parameter_name"] == "flame_temperature"][0]
    assert row["status"] == "comparable"


def test_missing_experiment_404(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-001", "exp-nope"]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_missing_hardware_404(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/hardware", json={"hardware_ids": ["hw-cir", "hw-nope"]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Hardware not found"


def test_missing_measurement_404(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/measurements", json={"measurement_ids": ["m-001", "m-nope"]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Measurement not found"


def test_duplicate_ids_400(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-001", "exp-001"]})
    assert response.status_code == 400


def test_single_id_422(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-001"]})
    assert response.status_code == 422


def test_too_many_ids_422(client):
    test_client, _, _ = client
    ids = [f"exp-{number:03d}" for number in range(1, 12)]
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ids})
    assert response.status_code == 422


def test_unknown_parameter_400(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-001", "exp-002"], "parameters": ["no_such_parameter"]})
    assert response.status_code == 400


def test_incompatible_units_not_comparable(client):
    test_client, exp_repo, _ = client
    exp_repo.create(_experiment("exp-003", "Synthetic Third Test", [_measurement("m-003", "exp-003", unit="C")], _conditions()))
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-001", "exp-003"]})
    assert response.status_code == 200
    data = response.json()
    row = [item for item in data["parameters"] if item["parameter_name"] == "flame_temperature"][0]
    assert row["status"] == "not_comparable"
    assert data["incompatible_items"]


def test_different_gravity_partially_comparable(client):
    test_client, exp_repo, _ = client
    exp_repo.create(_experiment("exp-003", "Synthetic Third Test", [_measurement("m-003", "exp-003")], _conditions(gravity="lunar")))
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-001", "exp-003"]})
    assert response.status_code == 200
    data = response.json()
    row = [item for item in data["parameters"] if item["parameter_name"] == "flame_temperature"][0]
    assert row["status"] == "partially_comparable"


def test_empty_dataset_404(client):
    test_client, _, _ = client
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-001", "exp-002"]})
    assert response.status_code == 200
    response = test_client.post("/api/v1/comparisons/experiments", json={"experiment_ids": ["exp-101", "exp-102"]})
    assert response.status_code == 404


def test_previous_modules_still_work(client):
    test_client, _, _ = client
    health = test_client.get("/api/health")
    assert health.status_code == 200
    experiments = test_client.get("/api/v1/experiments")
    assert experiments.status_code == 200
    assert experiments.json()["total"] == 0
    hardware = test_client.get("/api/v1/hardware")
    assert hardware.status_code == 200
    assert hardware.json()["total"] == 0
