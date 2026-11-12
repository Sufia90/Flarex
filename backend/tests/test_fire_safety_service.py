import pytest

from app.repositories.experiment_repository import ExperimentNotFoundError, ExperimentRepository
from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.common import VerificationStatus
from app.schemas.experiment import Experiment, ExperimentalConditions, Finding
from app.schemas.fire_safety import FireSafetyCategory, FireSafetyEvidenceStatus
from app.schemas.hardware import Hardware, HardwareType
from app.schemas.relationship import ExperimentHardwareRelationship
from app.services.fire_safety_service import FireSafetyService


def _conditions():
    return ExperimentalConditions(
        fuel_material="methanol",
        oxygen_concentration=21.0,
        oxygen_unit="%",
        gravity_condition="microgravity",
    )


def _finding(finding_id, experiment_id, categories=None, observation="Methanol flame behaviour was observed.", conclusion="The observation supports further study.", source_id="src-f-001"):
    return Finding(
        id=finding_id,
        experiment_id=experiment_id,
        title="Synthetic finding",
        observation=observation,
        conclusion=conclusion,
        fire_safety_relevance=categories or [],
        source_id=source_id,
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
        conditions=_conditions(),
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
    service = FireSafetyService(experiment_repository=exp_repo, hardware_repository=hw_repo, relationship_repository=rel_repo)
    return service, exp_repo, hw_repo, rel_repo


def test_prevention_evidence_retrieval(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["prevention"])], ["src-001"]))
    insights = service.get_insights_by_category(FireSafetyCategory.PREVENTION)
    assert len(insights) == 1
    insight = insights[0]
    assert insight.category == FireSafetyCategory.PREVENTION
    assert insight.evidence_status == FireSafetyEvidenceStatus.DOCUMENTED
    assert insight.experiment_id == "exp-001"
    assert insight.finding_ids == ["f-001"]
    assert "src-001" in insight.source_ids
    assert "src-f-001" in insight.source_ids
    assert any("Methanol flame behaviour" in item for item in insight.documented_evidence)


def test_detection_evidence_retrieval(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic SAME Test", ["detection"], [_finding("f-001", "exp-001", ["detection"], observation="Smoke was observed by the sensor.")], ["src-001"]))
    insights = service.get_insights_by_category(FireSafetyCategory.DETECTION)
    assert len(insights) == 1
    assert insights[0].evidence_status == FireSafetyEvidenceStatus.DOCUMENTED
    assert any("Smoke was observed" in item for item in insights[0].documented_evidence)


def test_suppression_evidence_retrieval(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic Suppression Test", ["suppression"], [_finding("f-001", "exp-001", ["suppression"], observation="Flame size reduced after the method was applied.")], ["src-001"]))
    insights = service.get_insights_by_category(FireSafetyCategory.SUPPRESSION)
    assert len(insights) == 1
    assert insights[0].evidence_status == FireSafetyEvidenceStatus.DOCUMENTED


def test_one_experiment_multiple_categories(setup):
    service, exp_repo, _, _ = setup
    findings = [
        _finding("f-001", "exp-001", ["prevention"]),
        _finding("f-002", "exp-001", ["detection"], observation="Smoke was observed by the sensor."),
        _finding("f-003", "exp-001", ["suppression"], observation="Flame size reduced after the method was applied."),
    ]
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention", "detection", "suppression"], findings, ["src-001"]))
    insights = service.get_insights_for_experiment("exp-001")
    assert len(insights) == 3
    assert {insight.category for insight in insights} == {FireSafetyCategory.PREVENTION, FireSafetyCategory.DETECTION, FireSafetyCategory.SUPPRESSION}
    assert all(insight.evidence_status == FireSafetyEvidenceStatus.DOCUMENTED for insight in insights)


def test_experiment_no_category(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", [], [_finding("f-001", "exp-001", [])], ["src-001"]))
    assert service.get_insights_for_experiment("exp-001") == []
    assert service.get_all_insights() == []


def test_missing_findings(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [], ["src-001"]))
    insights = service.get_insights_for_experiment("exp-001")
    assert len(insights) == 1
    assert insights[0].evidence_status == FireSafetyEvidenceStatus.INSUFFICIENT_EVIDENCE
    assert insights[0].missing_information


def test_missing_source_references(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["prevention"], source_id=None)], []))
    insights = service.get_insights_for_experiment("exp-001")
    assert insights[0].evidence_status == FireSafetyEvidenceStatus.POTENTIAL
    assert insights[0].source_ids == []
    assert any("No source references" in item for item in insights[0].limitations)


def test_unknown_evidence_status(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [], []))
    result = service.get_insight_for_experiment_category("exp-001", FireSafetyCategory.DETECTION)
    assert result.evidence_status == FireSafetyEvidenceStatus.UNKNOWN
    assert result.documented_evidence == []
    assert result.potential_applications == []


def test_unsupported_classification(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["prevention"])], ["src-001"]))
    result = service.get_insight_for_experiment_category("exp-001", FireSafetyCategory.SUPPRESSION)
    assert result.evidence_status == FireSafetyEvidenceStatus.UNSUPPORTED
    assert result.documented_evidence == []
    assert result.potential_applications == []


def test_potential_vs_documented(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["prevention"])], ["src-001"]))
    insight = service.get_insights_for_experiment("exp-001")[0]
    assert insight.evidence_status == FireSafetyEvidenceStatus.DOCUMENTED
    assert any("Methanol flame behaviour" in item for item in insight.documented_evidence)
    assert insight.potential_applications
    assert not any("Methanol flame behaviour" in item for item in insight.potential_applications)
    assert any("requires further validation" in item for item in insight.potential_applications)
    assert insight.documented_evidence != insight.potential_applications


def test_filter_by_experiment(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["prevention"])], ["src-001"]))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test", ["detection"], [_finding("f-002", "exp-002", ["detection"])], ["src-001"]))
    results = service.search_insights(experiment_id="exp-001")
    assert len(results) == 1
    assert results[0].experiment_id == "exp-001"


def test_filter_by_hardware(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["prevention"])], ["src-001"]))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    rel_repo.create(ExperimentHardwareRelationship(id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", relationship_type="used_in"))
    results = service.get_insights_for_hardware("hw-cir")
    assert len(results) == 1
    assert results[0].derived is True
    assert results[0].hardware_ids == ["hw-cir"]
    assert results[0].insight_id.startswith("fs-hw-hw-cir")
    assert "Derived from linked experiment exp-001" in results[0].explanation


def test_empty_dataset(setup):
    service, _, _, _ = setup
    assert service.get_all_insights() == []
    summary = service.get_summary()
    assert summary.total_experiments == 0
    assert summary.total_insights == 0
    assert summary.prevention_count == 0
    assert summary.detection_count == 0
    assert summary.suppression_count == 0
    assert summary.experiments_with_evidence == 0
    assert summary.experiments_without_evidence == 0


def test_invalid_experiment_id(setup):
    service, _, _, _ = setup
    with pytest.raises(ExperimentNotFoundError):
        service.get_insights_for_experiment("exp-nope")


def test_invalid_hardware_id(setup):
    service, _, _, _ = setup
    with pytest.raises(HardwareNotFoundError):
        service.get_insights_for_hardware("hw-nope")


def test_summary_counts(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention", "detection"], [_finding("f-001", "exp-001", ["prevention"])], ["src-001"]))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test", ["suppression"], [], []))
    summary = service.get_summary()
    assert summary.total_experiments == 2
    assert summary.total_insights == 3
    assert summary.prevention_count == 1
    assert summary.detection_count == 1
    assert summary.suppression_count == 1
    assert summary.documented_count == 1
    assert summary.potential_count == 1
    assert summary.insufficient_evidence_count == 1
    assert summary.unsupported_count == 0
    assert summary.unknown_count == 0
    assert summary.experiments_with_evidence == 2
    assert summary.experiments_without_evidence == 0


def test_filter_by_mission(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["prevention"])], ["src-001"], missions=["Moon"]))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test", ["prevention"], [_finding("f-002", "exp-002", ["prevention"])], ["src-001"], missions=["ISS"]))
    results = service.search_insights(mission="Moon")
    assert len(results) == 1
    assert results[0].experiment_id == "exp-001"
    with pytest.raises(ValueError, match="ISS, Moon, Mars"):
        service.search_insights(mission="Jupiter")


def test_original_records_not_modified(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["prevention"])], ["src-001"]))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    rel_repo.create(ExperimentHardwareRelationship(id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", relationship_type="used_in"))
    before_experiments = [item.model_dump() for item in exp_repo.get_all()]
    before_hardware = [item.model_dump() for item in hw_repo.get_all()]
    before_relationships = [item.model_dump() for item in rel_repo.get_all()]
    service.get_all_insights()
    service.get_insights_for_hardware("hw-cir")
    service.get_summary()
    assert [item.model_dump() for item in exp_repo.get_all()] == before_experiments
    assert [item.model_dump() for item in hw_repo.get_all()] == before_hardware
    assert [item.model_dump() for item in rel_repo.get_all()] == before_relationships


def test_unlisted_category_with_tagged_finding_is_documented(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["suppression"], observation="Flame size reduced after the method was applied.")], ["src-001"]))
    result = service.get_insight_for_experiment_category("exp-001", FireSafetyCategory.SUPPRESSION)
    assert result.category == FireSafetyCategory.SUPPRESSION
    assert result.evidence_status == FireSafetyEvidenceStatus.DOCUMENTED
    assert result.finding_ids == ["f-001"]
    assert any("Flame size reduced" in item for item in result.documented_evidence)
    assert "src-001" in result.source_ids
    assert "src-f-001" in result.source_ids
    assert result.verification_status == VerificationStatus.UNVERIFIED


def test_unlisted_category_with_tagged_finding_no_sources_is_potential(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], [_finding("f-001", "exp-001", ["suppression"], observation="Flame size reduced after the method was applied.", source_id=None)], []))
    result = service.get_insight_for_experiment_category("exp-001", FireSafetyCategory.SUPPRESSION)
    assert result.evidence_status == FireSafetyEvidenceStatus.POTENTIAL
    assert result.finding_ids == ["f-001"]
    assert result.source_ids == []
    assert result.potential_applications
    assert any("No source references" in item for item in result.limitations)
    assert result.verification_status == VerificationStatus.UNVERIFIED


def test_finding_tagged_category_appears_in_experiment_insights(setup):
    service, exp_repo, _, _ = setup
    findings = [
        _finding("f-001", "exp-001", ["prevention"]),
        _finding("f-002", "exp-001", ["suppression"], observation="Flame size reduced after the method was applied."),
    ]
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", ["prevention"], findings, ["src-001"]))
    insights = service.get_insights_for_experiment("exp-001")
    assert len(insights) == 2
    assert {insight.category for insight in insights} == {FireSafetyCategory.PREVENTION, FireSafetyCategory.SUPPRESSION}
    suppression = next(insight for insight in insights if insight.category == FireSafetyCategory.SUPPRESSION)
    assert suppression.evidence_status == FireSafetyEvidenceStatus.DOCUMENTED
    assert suppression.finding_ids == ["f-002"]
