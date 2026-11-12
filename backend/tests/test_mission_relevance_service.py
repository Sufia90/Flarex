import pytest

from app.repositories.experiment_repository import ExperimentNotFoundError, ExperimentRepository
from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment, ExperimentalConditions, Finding
from app.schemas.hardware import Hardware, HardwareType
from app.schemas.mission_relevance import MissionContext, RelevanceLevel
from app.schemas.relationship import ExperimentHardwareRelationship
from app.services.mission_relevance_service import MissionRelevanceService


def _conditions(gravity="microgravity"):
    return ExperimentalConditions(
        fuel_material="methanol",
        oxygen_concentration=21.0,
        oxygen_unit="%",
        gravity_condition=gravity,
    )


def _finding(finding_id, experiment_id):
    return Finding(id=finding_id, experiment_id=experiment_id, title="Synthetic finding", source_id="src-f-001")


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
def setup(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    rel_repo = RelationshipRepository(data_dir=tmp_path / "relationships")
    service = MissionRelevanceService(experiment_repository=exp_repo, hardware_repository=hw_repo, relationship_repository=rel_repo)
    return service, exp_repo, hw_repo, rel_repo


def test_iss_relevance_documented(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["ISS"], "Applies to ISS fire safety.", _conditions(), [_finding("f-001", "exp-001")], ["src-001"]))
    result = service.assess_experiment("exp-001", "ISS")
    assert result.mission == MissionContext.ISS
    assert result.relevance_level == RelevanceLevel.DOCUMENTED
    assert result.subject_type == "experiment"
    assert any("ISS" in item for item in result.similarities)
    assert any("microgravity" in item for item in result.similarities)
    assert "src-001" in result.source_ids
    assert "src-f-001" in result.source_ids


def test_moon_relevance_documented(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["Moon"], "May transfer to lunar gravity.", _conditions()))
    result = service.assess_experiment("exp-001", "moon")
    assert result.mission == MissionContext.MOON
    assert result.relevance_level == RelevanceLevel.DOCUMENTED


def test_mars_relevance_potential(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["Mars"], None, _conditions()))
    result = service.assess_experiment("exp-001", "Mars")
    assert result.relevance_level == RelevanceLevel.POTENTIAL


def test_potential_note_without_listing(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", [], "Transferability to other missions is discussed.", _conditions()))
    result = service.assess_experiment("exp-001", "Moon")
    assert result.relevance_level == RelevanceLevel.POTENTIAL


def test_unsupported_relevance(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", [], None, _conditions()))
    result = service.assess_experiment("exp-001", "Moon")
    assert result.relevance_level == RelevanceLevel.UNSUPPORTED
    assert any("Microgravity findings do not automatically transfer" in item for item in result.transferability_limitations)


def test_unknown_relevance(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", [], None, _conditions(gravity="earth gravity")))
    result = service.assess_experiment("exp-001", "Mars")
    assert result.relevance_level == RelevanceLevel.UNKNOWN


def test_missing_mission_evidence(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test"))
    result = service.assess_experiment("exp-001", "Moon")
    assert result.relevance_level == RelevanceLevel.INSUFFICIENT_EVIDENCE
    assert result.missing_information


def test_microgravity_partial_gravity_limitation(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["Moon"], "May transfer to lunar gravity.", _conditions()))
    result = service.assess_experiment("exp-001", "Moon")
    assert result.relevance_level == RelevanceLevel.DOCUMENTED
    assert any("partial gravity" in item for item in result.differences)
    assert any("Microgravity findings do not automatically transfer" in item for item in result.limitations)


def test_missing_experiment(setup):
    service, _, _, _ = setup
    with pytest.raises(ExperimentNotFoundError):
        service.assess_experiment("exp-nope", "Moon")


def test_missing_hardware(setup):
    service, _, _, _ = setup
    with pytest.raises(HardwareNotFoundError):
        service.assess_hardware("hw-nope", "Moon")


def test_invalid_mission(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test"))
    with pytest.raises(ValueError, match="ISS, Moon, Mars"):
        service.assess_experiment("exp-001", "Jupiter")


def test_no_invented_mission_score(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["ISS"], "Applies to ISS fire safety.", _conditions(), [_finding("f-001", "exp-001")], ["src-001"]))
    result = service.assess_experiment("exp-001", "ISS")
    assert not any("score" in key for key in result.model_dump().keys())
    assert "No numeric relevance score" in " ".join(result.limitations)


def test_source_references_preserved(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["ISS"], "Applies to ISS fire safety.", _conditions(), [_finding("f-001", "exp-001")], ["src-001"]))
    result = service.assess_experiment("exp-001", "ISS")
    assert "src-001" in result.source_ids
    assert "src-f-001" in result.source_ids
    assert any("Finding: Synthetic finding" in item for item in result.supporting_evidence)


def test_hardware_relevance_derived(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["Moon"], "May transfer to lunar gravity.", _conditions()))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test", [], None, _conditions(gravity="earth gravity")))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    rel_repo.create(ExperimentHardwareRelationship(id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", relationship_type="used_in"))
    rel_repo.create(ExperimentHardwareRelationship(id="rel-002", experiment_id="exp-002", hardware_id="hw-cir", relationship_type="used_in"))
    result = service.assess_hardware("hw-cir", "Moon")
    assert result.subject_type == "hardware"
    assert result.relevance_level == RelevanceLevel.DOCUMENTED
    assert result.derived_from_experiment_ids == ["exp-001", "exp-002"]
    assert any("exp-001: documented" in item for item in result.supporting_evidence)
    assert any("exp-002: unknown" in item for item in result.supporting_evidence)
    assert any("derived from linked experiments" in item.lower() for item in result.limitations)


def test_hardware_no_linked_experiments(setup):
    service, _, hw_repo, _ = setup
    hw_repo.create(_hardware("hw-empty", "Synthetic Empty"))
    result = service.assess_hardware("hw-empty", "Moon")
    assert result.relevance_level == RelevanceLevel.INSUFFICIENT_EVIDENCE
    assert result.derived_from_experiment_ids == []


def test_original_records_not_modified(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["Moon"], "May transfer to lunar gravity.", _conditions()))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    rel_repo.create(ExperimentHardwareRelationship(id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", relationship_type="used_in"))
    before_experiments = [item.model_dump() for item in exp_repo.get_all()]
    before_hardware = [item.model_dump() for item in hw_repo.get_all()]
    before_relationships = [item.model_dump() for item in rel_repo.get_all()]
    service.assess_experiment("exp-001", "Moon")
    service.assess_hardware("hw-cir", "Moon")
    assert [item.model_dump() for item in exp_repo.get_all()] == before_experiments
    assert [item.model_dump() for item in hw_repo.get_all()] == before_hardware
    assert [item.model_dump() for item in rel_repo.get_all()] == before_relationships
