import pytest
from pydantic import ValidationError
from app.schemas.common import DataCompleteness
from app.schemas.experiment import Experiment, ExperimentalConditions, Finding, Measurement
from app.schemas.hardware import Hardware, HardwareType
from app.schemas.relationship import ExperimentHardwareRelationship, MediaReference, Source
from app.services.validation import compute_data_quality


def valid_experiment_data():
    return {"id": "synthetic-exp-001", "nasa_investigation_id": "SYN-001", "name": "Synthetic FLEX example", "acronym": "SYN-FLEX", "description": "Synthetic test record only", "scientific_objective": "Test only", "research_category": "droplet combustion", "combustion_type": "liquid", "fuel_material": "methanol", "hardware_ids": ["synthetic-hw-001"], "conditions": {"fuel_material": "methanol", "oxygen_concentration": 21.0, "oxygen_unit": "%", "ambient_pressure": 101.3, "pressure_unit": "kPa"}, "source_ids": ["synthetic-src-001"]}


def test_valid_experiment():
    exp = Experiment(**valid_experiment_data())
    assert exp.id == "synthetic-exp-001"
    assert exp.conditions.oxygen_concentration == 21.0
    assert exp.data_quality.completeness == DataCompleteness.NOT_YET_VERIFIED


def test_incomplete_experiment():
    exp = Experiment(id="synthetic-exp-002", name="Synthetic incomplete example")
    assert exp.description is None
    assert exp.conditions is None
    assert exp.hardware_ids == []
    assert compute_data_quality(exp).completeness == DataCompleteness.INCOMPLETE


def test_valid_hardware():
    hw = Hardware(id="synthetic-hw-001", name="Synthetic CIR example", acronym="SYN-CIR", hardware_type=HardwareType.FACILITY)
    assert hw.hardware_type == HardwareType.FACILITY


def test_hardware_type_distinctions():
    cir = Hardware(id="synthetic-hw-cir", name="Synthetic CIR", hardware_type="facility")
    mdca = Hardware(id="synthetic-hw-mdca", name="Synthetic MDCA", hardware_type="apparatus", parent_hardware_id="synthetic-hw-cir")
    msg = Hardware(id="synthetic-hw-msg", name="Synthetic MSG", hardware_type="facility")
    assert cir.hardware_type != mdca.hardware_type
    assert cir.hardware_type == msg.hardware_type
    assert mdca.parent_hardware_id == "synthetic-hw-cir"


def test_valid_relationship():
    rel = ExperimentHardwareRelationship(id="synthetic-rel-001", experiment_id="synthetic-exp-001", hardware_id="synthetic-hw-001", relationship_type="used_in", verification_status="confirmed")
    assert rel.verification_status.value == "confirmed"


def test_invalid_relationship_self_reference():
    with pytest.raises(ValidationError):
        ExperimentHardwareRelationship(id="synthetic-rel-002", experiment_id="same-id", hardware_id="same-id")


def test_missing_oxygen_and_pressure():
    exp = Experiment(id="synthetic-exp-003", name="Synthetic missing conditions", conditions=ExperimentalConditions(fuel_material="methanol"))
    assert exp.conditions.oxygen_concentration is None
    assert exp.conditions.ambient_pressure is None


def test_zero_vs_unknown_measurement():
    zero = Measurement(id="synthetic-m-001", experiment_id="synthetic-exp-001", parameter_name="burning rate", value=0.0, unit="mm/s")
    unknown = Measurement(id="synthetic-m-002", experiment_id="synthetic-exp-001", parameter_name="burning rate", value=None, unit=None)
    assert zero.value == 0.0
    assert zero.value is not None
    assert unknown.value is None


def test_numeric_and_categorical_measurements():
    numeric = Measurement(id="synthetic-m-003", experiment_id="synthetic-exp-001", parameter_name="flame temperature", value=1200.0, unit="K")
    categorical = Measurement(id="synthetic-m-004", experiment_id="synthetic-exp-001", parameter_name="outcome", value="extinction", unit=None)
    boolean = Measurement(id="synthetic-m-005", experiment_id="synthetic-exp-001", parameter_name="ignition observed", value=True, unit=None)
    assert isinstance(numeric.value, float)
    assert categorical.value == "extinction"
    assert boolean.value is True


def test_valid_and_invalid_measurement_units():
    valid = Measurement(id="synthetic-m-006", experiment_id="synthetic-exp-001", parameter_name="flame diameter", value=5.0, unit="mm")
    assert valid.unit == "mm"
    with pytest.raises(ValidationError):
        Measurement(id="synthetic-m-007", experiment_id="synthetic-exp-001", parameter_name="flame diameter", value={"bad": 1}, unit="mm")


def test_valid_source():
    src = Source(id="synthetic-src-001", source_type="dataset", title="Synthetic source example", doi="10.60555/synthetic-001", url="https://example.org/synthetic")
    assert src.doi.startswith("10.")


def test_invalid_source_url_and_doi():
    with pytest.raises(ValidationError):
        Source(id="synthetic-src-002", title="Bad source", url="not-a-url")
    with pytest.raises(ValidationError):
        Source(id="synthetic-src-003", title="Bad DOI", doi="12345")


def test_finding_keeps_observation_separate():
    f = Finding(id="synthetic-f-001", experiment_id="synthetic-exp-001", title="Synthetic finding", observation="Observed in test data", conclusion="Test conclusion only")
    assert f.observation != f.conclusion


def test_media_reference():
    m = MediaReference(id="synthetic-media-001", file_path="media/hardware/synthetic.jpg", media_type="image", hardware_id="synthetic-hw-001", credit="Synthetic test credit")
    assert m.hardware_id == "synthetic-hw-001"
import pytest
from pydantic import ValidationError


def test_measurement_kind_valid_values():
    for kind in ["measured", "derived", "interpreted"]:
        measurement = Measurement(
            id="m-001",
            experiment_id="exp-001",
            parameter_name="oxygen concentration",
            value=20.0,
            unit="%",
            measurement_kind=kind,
        )
        assert measurement.measurement_kind == kind


def test_measurement_kind_default_is_none():
    measurement = Measurement(
        id="m-001",
        experiment_id="exp-001",
        parameter_name="oxygen concentration",
        value=20.0,
        unit="%",
    )
    assert measurement.measurement_kind is None


def test_measurement_kind_invalid_value():
    with pytest.raises(ValidationError):
        Measurement(
            id="m-001",
            experiment_id="exp-001",
            parameter_name="oxygen concentration",
            value=20.0,
            unit="%",
            measurement_kind="estimated",
        )


def test_experiment_new_fields_valid():
    experiment = Experiment(
        id="exp-001",
        name="Synthetic FLEX test",
        mission_applicability=["ISS", "Moon"],
        transferability_note="Microgravity result, Mars transfer needs check",
        fire_safety_relevance=["prevention", "detection"],
    )
    assert experiment.mission_applicability == ["ISS", "Moon"]
    assert experiment.transferability_note == "Microgravity result, Mars transfer needs check"
    assert experiment.fire_safety_relevance == ["prevention", "detection"]


def test_experiment_new_fields_invalid_values():
    with pytest.raises(ValidationError):
        Experiment(
            id="exp-001",
            name="Synthetic FLEX test",
            mission_applicability=["Earth"],
        )
    with pytest.raises(ValidationError):
        Experiment(
            id="exp-001",
            name="Synthetic FLEX test",
            fire_safety_relevance=["extinguishing"],
        )


def test_old_record_without_new_fields():
    experiment = Experiment(id="exp-001", name="Old synthetic record")
    assert experiment.mission_applicability == []
    assert experiment.transferability_note is None
    assert experiment.fire_safety_relevance == []
    measurement = Measurement(
        id="m-001",
        experiment_id="exp-001",
        parameter_name="oxygen concentration",
        value=20.0,
        unit="%",
    )
    assert measurement.measurement_kind is None


def test_empty_list_defaults_are_independent():
    first = Experiment(id="exp-001", name="First synthetic record")
    second = Experiment(id="exp-002", name="Second synthetic record")
    first.mission_applicability.append("ISS")
    first.fire_safety_relevance.append("prevention")
    assert second.mission_applicability == []
    assert second.fire_safety_relevance == []


def test_missing_versus_zero():
    missing = Measurement(
        id="m-001",
        experiment_id="exp-001",
        parameter_name="oxygen concentration",
        value=None,
        unit="%",
    )
    assert missing.value is None
    assert missing.measurement_kind is None
    zero = Measurement(
        id="m-002",
        experiment_id="exp-001",
        parameter_name="oxygen concentration",
        value=0.0,
        unit="%",
    )
    assert zero.value == 0.0
    assert zero.value is not None


def test_existing_experiment_fields_still_work():
    experiment = Experiment(
        id="exp-001",
        name="Synthetic FLEX test",
        description="Synthetic record for schema compatibility check",
        fuel_material="methanol",
        hardware_ids=["CIR"],
    )
    assert experiment.name == "Synthetic FLEX test"
    assert experiment.fuel_material == "methanol"
    assert experiment.hardware_ids == ["CIR"]


def test_compute_data_quality_missing_fields_lists_absent_signals():
    exp = Experiment(**valid_experiment_data())
    quality = compute_data_quality(exp)
    assert quality.completeness == DataCompleteness.PARTIALLY_COMPLETE
    assert quality.missing_fields == ["measurements", "findings"]


def test_compute_data_quality_complete_record_has_no_missing_fields():
    exp = Experiment(
        **valid_experiment_data(),
        measurements=[Measurement(id="synthetic-m-101", experiment_id="synthetic-exp-001", parameter_name="flame temperature", value=1200.0, unit="K")],
        findings=[Finding(id="synthetic-f-101", experiment_id="synthetic-exp-001", title="Synthetic finding", observation="Observed in test data")],
    )
    quality = compute_data_quality(exp)
    assert quality.completeness == DataCompleteness.COMPLETE
    assert quality.missing_fields == []


def test_compute_data_quality_incomplete_record_lists_all_signals():
    exp = Experiment(id="synthetic-exp-002", name="Synthetic incomplete example")
    quality = compute_data_quality(exp)
    assert quality.completeness == DataCompleteness.INCOMPLETE
    assert quality.missing_fields == ["description", "scientific_objective", "research_category", "conditions", "source_ids", "measurements", "findings"]
