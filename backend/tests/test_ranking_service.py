import pytest

from app.repositories.experiment_repository import ExperimentNotFoundError, ExperimentRepository
from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment, ExperimentalConditions, Finding, Measurement
from app.schemas.hardware import Hardware, HardwareType
from app.schemas.ranking import RankingCriterion, RankingRequest, RankingStatus
from app.schemas.relationship import ExperimentHardwareRelationship
from app.services.ranking_service import RankingService


def _measurement(measurement_id, experiment_id, parameter="flame_temperature", kind="measured"):
    return Measurement(
        id=measurement_id,
        experiment_id=experiment_id,
        parameter_name=parameter,
        value=1000.0,
        unit="K",
        measurement_kind=kind,
        measurement_method="thermocouple",
        source_id="src-m-001",
    )


def _experiment(experiment_id, name, measurements=None, conditions=None, findings=None, source_ids=None, description=None, objective=None, category=None, limitations=None):
    return Experiment(
        id=experiment_id,
        name=name,
        description=description,
        scientific_objective=objective,
        research_category=category,
        conditions=conditions,
        measurements=measurements or [],
        findings=findings or [],
        limitations=limitations or [],
        source_ids=source_ids or [],
    )


def _conditions():
    return ExperimentalConditions(
        fuel_material="methanol",
        oxygen_concentration=21.0,
        oxygen_unit="%",
        gravity_condition="microgravity",
    )


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
def setup(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    rel_repo = RelationshipRepository(data_dir=tmp_path / "relationships")
    service = RankingService(experiment_repository=exp_repo, hardware_repository=hw_repo, relationship_repository=rel_repo)
    return service, exp_repo, hw_repo, rel_repo


def _seed_hardware_case(exp_repo, hw_repo, rel_repo):
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test"))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test"))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    hw_repo.create(_hardware("hw-msg", "Synthetic MSG"))
    hw_repo.create(_hardware("hw-empty", "Synthetic Empty"))
    rel_repo.create(_relationship("rel-001", "exp-001", "hw-cir"))
    rel_repo.create(_relationship("rel-002", "exp-002", "hw-cir"))
    rel_repo.create(_relationship("rel-003", "exp-001", "hw-msg"))


def _item(result, item_id):
    for item in result.items:
        if item.item_id == item_id:
            return item
    raise AssertionError(f"item {item_id} not found")


def test_hardware_associations_ranking(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    _seed_hardware_case(exp_repo, hw_repo, rel_repo)
    result = service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS))
    assert result.status == RankingStatus.RANKED
    assert _item(result, "hw-cir").rank == 1
    assert _item(result, "hw-cir").metric_value == 2
    assert _item(result, "hw-msg").rank == 2
    assert _item(result, "hw-msg").metric_value == 1
    assert _item(result, "hw-empty").rank is None
    assert _item(result, "hw-empty").metric_value == 0
    assert "rel-001" in _item(result, "hw-cir").evidence_ids


def test_deterministic_ranking(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    _seed_hardware_case(exp_repo, hw_repo, rel_repo)
    first = service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS))
    second = service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS))
    assert [(item.item_id, item.rank, item.metric_value) for item in first.items] == [(item.item_id, item.rank, item.metric_value) for item in second.items]


def test_documentation_completeness(setup):
    service, exp_repo, _, _ = setup
    finding = Finding(id="f-001", experiment_id="exp-full", title="Synthetic finding")
    exp_repo.create(_experiment("exp-full", "Synthetic Full Test", [_measurement("m-001", "exp-full")], _conditions(), [finding], ["src-001"], "A description.", "An objective.", "flammability", ["Some limitations."]))
    exp_repo.create(_experiment("exp-thin", "Synthetic Thin Test"))
    result = service.rank(RankingRequest(criterion=RankingCriterion.EXPERIMENT_DOCUMENTATION_COMPLETENESS))
    assert result.status == RankingStatus.RANKED
    assert result.metric_max == 9
    assert _item(result, "exp-full").rank == 1
    assert _item(result, "exp-full").metric_value == 9
    assert _item(result, "exp-thin").rank == 2
    assert _item(result, "exp-thin").metric_value == 1
    assert _item(result, "exp-full").metric_breakdown["measurements"] == 1
    assert _item(result, "exp-thin").metric_breakdown["measurements"] == 0


def test_measurement_coverage(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-a", "Synthetic A Test", [_measurement("m-001", "exp-a"), _measurement("m-002", "exp-a", "oxygen_concentration"), _measurement("m-003", "exp-a", kind="derived")]))
    exp_repo.create(_experiment("exp-b", "Synthetic B Test", [_measurement("m-004", "exp-b")]))
    exp_repo.create(_experiment("exp-c", "Synthetic C Test"))
    result = service.rank(RankingRequest(criterion=RankingCriterion.EXPERIMENT_MEASUREMENT_COVERAGE))
    assert result.status == RankingStatus.RANKED
    assert _item(result, "exp-a").rank == 1
    assert _item(result, "exp-a").metric_value == 3
    assert _item(result, "exp-a").metric_breakdown["measured"] == 2
    assert _item(result, "exp-a").metric_breakdown["derived"] == 1
    assert _item(result, "exp-a").metric_breakdown["distinct_parameters"] == 2
    assert _item(result, "exp-b").rank == 2
    assert _item(result, "exp-c").rank is None
    assert _item(result, "exp-c").metric_value == 0


def test_missing_data_not_treated_as_zero(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-a", "Synthetic A Test", [_measurement("m-001", "exp-a")]))
    exp_repo.create(_experiment("exp-b", "Synthetic B Test"))
    result = service.rank(RankingRequest(criterion=RankingCriterion.EXPERIMENT_MEASUREMENT_COVERAGE))
    item = _item(result, "exp-b")
    assert item.metric_value == 0
    assert item.rank is None
    assert "not ranked" in " ".join(item.limitations).lower() or "missing evidence" in item.explanation.lower()


def test_insufficient_evidence(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test"))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR"))
    hw_repo.create(_hardware("hw-msg", "Synthetic MSG"))
    rel_repo.create(_relationship("rel-001", "exp-001", "hw-cir"))
    result = service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS))
    assert result.status == RankingStatus.INSUFFICIENT_EVIDENCE
    assert all(item.rank is None for item in result.items)
    assert "Insufficient evidence" in result.explanation


def test_no_arbitrary_default_ranking(setup):
    service, _, _, _ = setup
    result = service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS))
    assert result.status == RankingStatus.INSUFFICIENT_EVIDENCE
    assert result.items == []
    assert result.eligible_item_ids == []


def test_transparent_methodology(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    _seed_hardware_case(exp_repo, hw_repo, rel_repo)
    result = service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS))
    assert result.methodology
    assert "Sort by count descending" in result.methodology
    assert result.metric_name == "distinct_experiment_associations"
    assert result.metric_description
    assert result.explanation
    assert result.limitations
    assert any("not hardware performance" in item for item in result.limitations)


def test_invalid_item_404(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test"))
    with pytest.raises(ExperimentNotFoundError):
        service.rank(RankingRequest(criterion=RankingCriterion.EXPERIMENT_MEASUREMENT_COVERAGE, item_ids=["exp-001", "exp-nope"]))
    with pytest.raises(HardwareNotFoundError):
        service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS, item_ids=["hw-nope"]))


def test_duplicate_item_ids(setup):
    service, exp_repo, _, _ = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test"))
    with pytest.raises(ValueError, match="Duplicate"):
        service.rank(RankingRequest(criterion=RankingCriterion.EXPERIMENT_MEASUREMENT_COVERAGE, item_ids=["exp-001", "exp-001"]))


def test_tie_shares_rank(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test"))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test"))
    hw_repo.create(_hardware("hw-top", "Synthetic Top"))
    hw_repo.create(_hardware("hw-a", "Synthetic A"))
    hw_repo.create(_hardware("hw-b", "Synthetic B"))
    rel_repo.create(_relationship("rel-001", "exp-001", "hw-top"))
    rel_repo.create(_relationship("rel-002", "exp-002", "hw-top"))
    rel_repo.create(_relationship("rel-003", "exp-001", "hw-a"))
    rel_repo.create(_relationship("rel-004", "exp-001", "hw-b"))
    result = service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS))
    assert _item(result, "hw-top").rank == 1
    assert _item(result, "hw-a").rank == 2
    assert _item(result, "hw-b").rank == 2


def test_limit_applied(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    _seed_hardware_case(exp_repo, hw_repo, rel_repo)
    result = service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS, limit=1))
    assert len(result.items) == 1
    assert len(result.eligible_item_ids) == 3
    assert any("limited to the first 1 items" in item for item in result.limitations)


def test_original_data_unchanged(setup):
    service, exp_repo, hw_repo, rel_repo = setup
    _seed_hardware_case(exp_repo, hw_repo, rel_repo)
    before_experiments = [item.model_dump() for item in exp_repo.get_all()]
    before_hardware = [item.model_dump() for item in hw_repo.get_all()]
    before_relationships = [item.model_dump() for item in rel_repo.get_all()]
    service.rank(RankingRequest(criterion=RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS))
    service.rank(RankingRequest(criterion=RankingCriterion.EXPERIMENT_MEASUREMENT_COVERAGE))
    assert [item.model_dump() for item in exp_repo.get_all()] == before_experiments
    assert [item.model_dump() for item in hw_repo.get_all()] == before_hardware
    assert [item.model_dump() for item in rel_repo.get_all()] == before_relationships
