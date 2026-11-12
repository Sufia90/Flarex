import pytest

from app.repositories.experiment_repository import ExperimentNotFoundError, ExperimentRepository
from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.schemas.comparison import ComparabilityStatus
from app.schemas.experiment import Experiment, ExperimentalConditions, Measurement
from app.schemas.hardware import Hardware, HardwareType
from app.services.comparison_service import ComparisonService, MeasurementNotFoundError


def _conditions(gravity="microgravity", oxygen=21.0, pressure=101.3, temperature=25.0, airflow=0.1):
    return ExperimentalConditions(
        fuel_material="methanol",
        oxygen_concentration=oxygen,
        oxygen_unit="%",
        oxygen_basis="mole",
        ambient_pressure=pressure,
        pressure_unit="kPa",
        temperature=temperature,
        temperature_unit="C",
        airflow_velocity=airflow,
        airflow_unit="m/s",
        gravity_condition=gravity,
        sample_geometry="droplet",
    )


def _measurement(measurement_id, experiment_id, parameter="flame_temperature", value=1000.0, unit="K", kind="measured", method="thermocouple", source="src-m-001"):
    return Measurement(
        id=measurement_id,
        experiment_id=experiment_id,
        parameter_name=parameter,
        value=value,
        unit=unit,
        measurement_kind=kind,
        measurement_method=method,
        sensor="TC-1",
        source_id=source,
    )


def _experiment(experiment_id, name, measurements=None, conditions=None):
    return Experiment(
        id=experiment_id,
        name=name,
        conditions=conditions,
        measurements=measurements or [],
        source_ids=["src-exp-001"],
    )


def _hardware(hardware_id, name, hardware_type=HardwareType.FACILITY, facility="rack", purpose="Test rack", measurements=None, experiments=None):
    return Hardware(
        id=hardware_id,
        name=name,
        hardware_type=hardware_type,
        facility_classification=facility,
        purpose=purpose,
        supported_measurements=measurements or [],
        related_experiment_ids=experiments or [],
        source_ids=["src-hw-001"],
    )


@pytest.fixture
def setup(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    service = ComparisonService(experiment_repository=exp_repo, hardware_repository=hw_repo)
    return service, exp_repo, hw_repo


def _seed_two_experiments(exp_repo, second_conditions=None, second_measurements=None):
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", [_measurement("m-001", "exp-001")], _conditions()))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test", second_measurements if second_measurements is not None else [_measurement("m-002", "exp-002")], second_conditions if second_conditions is not None else _conditions()))


def _row(result, parameter_name):
    for row in result.parameters:
        if row.parameter_name == parameter_name:
            return row
    raise AssertionError(f"parameter {parameter_name} not found")


def test_valid_experiment_comparison(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo)
    result = service.compare_experiments(["exp-001", "exp-002"])
    assert result.comparison_id == "cmp-exp-exp-001-exp-002"
    assert result.experiment_ids == ["exp-001", "exp-002"]
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.COMPARABLE
    assert row.values[0].value == 1000.0
    assert row.values[0].unit == "K"
    assert row.values[1].value == 1000.0
    assert any("flame_temperature is the same" in item for item in result.similarities)
    assert result.methodology
    assert result.explanation


def test_valid_hardware_comparison(setup):
    service, _, hw_repo = setup
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR", measurements=["temperature", "pressure"], experiments=["exp-001"]))
    hw_repo.create(_hardware("hw-msg", "Synthetic MSG", facility="glovebox", purpose="Test glovebox", measurements=["temperature", "imaging"], experiments=["exp-002"]))
    result = service.compare_hardware(["hw-cir", "hw-msg"])
    assert result.comparison_id == "cmp-hw-hw-cir-hw-msg"
    assert result.same_hardware_type is True
    assert result.shared_measurements == ["temperature"]
    assert result.unique_measurements["hw-cir"] == ["pressure"]
    assert result.unique_measurements["hw-msg"] == ["imaging"]
    assert any("hardware_type is the same" in item for item in result.similarities)


def test_measurement_comparison(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo, second_measurements=[_measurement("m-002", "exp-002", value=1100.0)])
    result = service.compare_measurements(["m-001", "m-002"])
    assert result.comparison_id == "cmp-meas-m-001-m-002"
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.COMPARABLE
    assert any("flame_temperature differs" in item for item in result.differences)


def test_missing_experiment_id(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo)
    with pytest.raises(ExperimentNotFoundError):
        service.compare_experiments(["exp-001", "exp-nope"])


def test_missing_hardware_id(setup):
    service, _, hw_repo = setup
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    with pytest.raises(HardwareNotFoundError):
        service.compare_hardware(["hw-cir", "hw-nope"])


def test_missing_measurement_id(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo)
    with pytest.raises(MeasurementNotFoundError):
        service.compare_measurements(["m-001", "m-nope"])


def test_duplicate_selected_ids(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo)
    with pytest.raises(ValueError, match="Duplicate"):
        service.compare_experiments(["exp-001", "exp-001"])


def test_single_id_rejected(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo)
    with pytest.raises(ValueError):
        service.compare_experiments(["exp-001"])


def test_unknown_parameter_rejected(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo)
    with pytest.raises(ValueError, match="Unknown parameters"):
        service.compare_experiments(["exp-001", "exp-002"], parameters=["no_such_parameter"])


def test_missing_measurement_values(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo, second_measurements=[])
    result = service.compare_experiments(["exp-001", "exp-002"])
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.PARTIALLY_COMPARABLE
    assert row.values[1].value is None
    assert row.values[1].missing_reason is not None
    assert any("exp-002" in item for item in result.missing_information)


def test_missing_units(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo, second_measurements=[_measurement("m-002", "exp-002", unit=None)])
    result = service.compare_experiments(["exp-001", "exp-002"])
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.NOT_COMPARABLE
    assert "no unit" in row.reason
    assert result.incompatible_items


def test_incompatible_units(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo, second_measurements=[_measurement("m-002", "exp-002", unit="C")])
    result = service.compare_experiments(["exp-001", "exp-002"])
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.NOT_COMPARABLE
    assert "Units differ" in row.reason
    assert any("flame_temperature" in item for item in result.incompatible_items)


def test_different_gravity_conditions(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo, second_conditions=_conditions(gravity="lunar"))
    result = service.compare_experiments(["exp-001", "exp-002"])
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.PARTIALLY_COMPARABLE
    assert "gravity condition" in row.reason
    gravity_row = [item for item in result.conditions if item.condition_name == "gravity_condition"][0]
    assert gravity_row.status == ComparabilityStatus.PARTIALLY_COMPARABLE


def test_different_oxygen_conditions(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo, second_conditions=_conditions(oxygen=30.0))
    result = service.compare_experiments(["exp-001", "exp-002"])
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.PARTIALLY_COMPARABLE
    assert "oxygen condition" in row.reason


def test_different_pressure_conditions(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo, second_conditions=_conditions(pressure=50.0))
    result = service.compare_experiments(["exp-001", "exp-002"])
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.PARTIALLY_COMPARABLE
    assert "pressure" in row.reason


def test_partially_comparable_measurements(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo, second_measurements=[_measurement("m-002", "exp-002", kind="derived")])
    result = service.compare_experiments(["exp-001", "exp-002"])
    row = _row(result, "flame_temperature")
    assert row.status == ComparabilityStatus.PARTIALLY_COMPARABLE
    assert "kinds differ" in row.reason


def test_insufficient_data_conditions(setup):
    service, exp_repo, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test"))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test"))
    result = service.compare_experiments(["exp-001", "exp-002"])
    assert result.parameters == []
    assert result.conditions
    assert all(row.status == ComparabilityStatus.INSUFFICIENT_DATA for row in result.conditions)
    assert any("No documented measurements" in item for item in result.limitations)


def test_source_references_preserved(setup):
    service, exp_repo, _ = setup
    _seed_two_experiments(exp_repo)
    result = service.compare_experiments(["exp-001", "exp-002"])
    assert "src-m-001" in result.source_ids
    assert "src-exp-001" in result.source_ids
    row = _row(result, "flame_temperature")
    assert row.values[0].source_id == "src-m-001"


def test_original_records_not_modified(setup):
    service, exp_repo, hw_repo = setup
    _seed_two_experiments(exp_repo)
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    hw_repo.create(_hardware("hw-msg", "Synthetic MSG"))
    before_experiments = [item.model_dump() for item in exp_repo.get_all()]
    before_hardware = [item.model_dump() for item in hw_repo.get_all()]
    service.compare_experiments(["exp-001", "exp-002"])
    service.compare_hardware(["hw-cir", "hw-msg"])
    service.compare_measurements(["m-001", "m-002"])
    assert [item.model_dump() for item in exp_repo.get_all()] == before_experiments
    assert [item.model_dump() for item in hw_repo.get_all()] == before_hardware


def test_hardware_different_types(setup):
    service, _, hw_repo = setup
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR", hardware_type=HardwareType.FACILITY))
    hw_repo.create(_hardware("hw-mdca", "Synthetic MDCA", hardware_type=HardwareType.APPARATUS))
    result = service.compare_hardware(["hw-cir", "hw-mdca"])
    assert result.same_hardware_type is False
    assert any("not directly interchangeable" in item for item in result.limitations)
