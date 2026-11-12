import pytest

from app.ai.config import AISettings
from app.ai.retrieval import RetrievalService
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.common import VerificationStatus
from app.schemas.experiment import Experiment, ExperimentalConditions, Finding, Measurement
from app.schemas.hardware import Hardware, HardwareType
from app.schemas.relationship import ExperimentHardwareRelationship, Source
from app.schemas.retrieval import RecordType, RetrievalRequest


def _conditions():
    return ExperimentalConditions(
        fuel_material="methanol",
        oxygen_concentration=21.0,
        oxygen_unit="%",
        gravity_condition="microgravity",
    )


def _experiment(experiment_id, name, full=False):
    if full:
        return Experiment(
            id=experiment_id,
            name=name,
            description="Methanol droplet combustion in microgravity.",
            scientific_objective="Study flame behaviour.",
            research_category="flammability",
            fuel_material="methanol",
            conditions=_conditions(),
            measurements=[Measurement(id="m-001", experiment_id=experiment_id, parameter_name="flame_temperature", parameter_description="Methanol flame temperature.", value=1000.0, unit="K", measurement_kind="measured", measurement_method="thermocouple", source_id="src-m-001")],
            findings=[Finding(id="f-001", experiment_id=experiment_id, title="Synthetic finding", observation="Methanol flame behaviour was observed.", fire_safety_relevance=["prevention"], source_id="src-f-001")],
            limitations=["Some limitations."],
            source_ids=["src-001"],
            fire_safety_relevance=["prevention"],
            mission_applicability=["Moon"],
        )
    return Experiment(
        id=experiment_id,
        name=name,
        description="Gas combustion study.",
    )


def _hardware(hardware_id, name, description):
    return Hardware(
        id=hardware_id,
        name=name,
        description=description,
        hardware_type=HardwareType.FACILITY,
        source_ids=["src-hw-001"],
    )


@pytest.fixture
def service(tmp_path):
    exp_repo = ExperimentRepository(data_dir=tmp_path / "experiments")
    hw_repo = HardwareRepository(data_dir=tmp_path / "hardware")
    rel_repo = RelationshipRepository(data_dir=tmp_path / "relationships")
    src_repo = SourceRepository(data_dir=tmp_path / "sources")
    exp_repo.create(_experiment("exp-001", "Synthetic FLEX Test", full=True))
    exp_repo.create(_experiment("exp-002", "Synthetic ACME Test"))
    hw_repo.create(_hardware("hw-cir", "Synthetic CIR", "Combustion Integrated Rack facility."))
    hw_repo.create(_hardware("hw-msg", "Synthetic MSG", "Microgravity Science Glovebox facility."))
    rel_repo.create(ExperimentHardwareRelationship(id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", relationship_type="used_in", role="housing", evidence="CIR housed the FLEX experiment."))
    src_repo.create(Source(id="src-001", source_type="nasa_report", title="FLEX Experiment Overview", nasa_report_id="PSI-69", doi="10.60555/mbq8-0451", publisher="NASA Glenn Research Center", description="FLEX investigation overview.", verification_status=VerificationStatus.CONFIRMED))
    src_repo.create(Source(id="src-f-001", source_type="paper", title="Methanol Flame Behaviour Notes", doi="10.1234/flame-notes", publisher="Flame Research Journal", description="Notes on methanol flame behaviour.", verification_status=VerificationStatus.CONFIRMED))
    src_repo.create(Source(id="src-m-001", source_type="dataset", title="Methanol Flame Temperature Data", doi="10.1234/flame-temp", publisher="NASA Glenn Research Center", description="Flame temperature measurements.", verification_status=VerificationStatus.VERIFICATION_FAILED))
    return RetrievalService(experiment_repository=exp_repo, hardware_repository=hw_repo, relationship_repository=rel_repo, source_repository=src_repo)


def _by_type(results, record_type):
    return [result for result in results if result.record_type == record_type]


def test_retrieval_from_experiment_records(service):
    result = service.search(RetrievalRequest(query="methanol"))
    experiments = _by_type(result.results, RecordType.EXPERIMENT)
    assert any(item.record_id == "exp-001" for item in experiments)
    item = next(item for item in experiments if item.record_id == "exp-001")
    assert item.experiment_id == "exp-001"
    assert item.source_ids == ["src-001"]
    assert "fuel_material" in item.matched_fields or "description" in item.matched_fields


def test_retrieval_from_finding_records(service):
    result = service.search(RetrievalRequest(query="flame behaviour"))
    findings = _by_type(result.results, RecordType.FINDING)
    assert any(item.record_id == "f-001" for item in findings)
    item = next(item for item in findings if item.record_id == "f-001")
    assert item.experiment_id == "exp-001"
    assert item.source_ids == ["src-f-001"]


def test_retrieval_from_measurement_records(service):
    result = service.search(RetrievalRequest(query="thermocouple"))
    measurements = _by_type(result.results, RecordType.MEASUREMENT)
    assert any(item.record_id == "m-001" for item in measurements)
    item = next(item for item in measurements if item.record_id == "m-001")
    assert item.experiment_id == "exp-001"
    assert item.evidence_category == "measured"


def test_retrieval_from_hardware_records(service):
    result = service.search(RetrievalRequest(query="rack"))
    hardware = _by_type(result.results, RecordType.HARDWARE)
    assert any(item.record_id == "hw-cir" for item in hardware)
    item = next(item for item in hardware if item.record_id == "hw-cir")
    assert item.hardware_id == "hw-cir"
    assert item.source_ids == ["src-hw-001"]


def test_retrieval_from_source_records(service):
    result = service.search(RetrievalRequest(query="methanol", record_types=[RecordType.SOURCE]))
    assert result.total == 2
    ids = {item.record_id for item in result.results}
    assert ids == {"src-f-001", "src-m-001"}
    item = next(item for item in result.results if item.record_id == "src-f-001")
    assert item.title == "Methanol Flame Behaviour Notes"
    assert item.source_ids == ["src-f-001"]
    assert item.verification_status == "confirmed"
    assert "title" in item.matched_fields
    assert not any("no dedicated repository" in text for text in result.limitations)
    full = service.search(RetrievalRequest(query="methanol"))
    experiments = _by_type(full.results, RecordType.EXPERIMENT)
    assert experiments[0].source_ids == ["src-001"]


def test_empty_retrieval_result(service):
    result = service.search(RetrievalRequest(query="zzzznope"))
    assert result.total == 0
    assert result.results == []
    assert "No relevant records" in result.explanation


def test_verification_status_preserved(service):
    result = service.search(RetrievalRequest(query="methanol"))
    experiments = _by_type(result.results, RecordType.EXPERIMENT)
    assert experiments[0].verification_status == "unverified"
    findings = _by_type(result.results, RecordType.FINDING)
    assert findings[0].verification_status == "unverified"


def test_limitations_preserved(service):
    result = service.search(RetrievalRequest(query="methanol"))
    experiments = _by_type(result.results, RecordType.EXPERIMENT)
    assert "Some limitations." in experiments[0].limitations
    assert "Keyword matching only" in " ".join(result.limitations)


def test_record_type_filter(service):
    result = service.search(RetrievalRequest(query="combustion", record_types=[RecordType.HARDWARE]))
    assert result.total >= 1
    assert all(item.record_type == RecordType.HARDWARE for item in result.results)


def test_experiment_filter(service):
    result = service.search(RetrievalRequest(query="flame", experiment_id="exp-001"))
    assert result.total >= 1
    assert all(item.experiment_id == "exp-001" for item in result.results)


def test_limit_applied(service):
    result = service.search(RetrievalRequest(query="combustion", limit=2))
    assert result.total == 3
    assert len(result.results) == 2


def test_empty_query_raises(service):
    with pytest.raises(ValueError, match="query must not be empty"):
        service.search(RetrievalRequest(query="  "))


def test_case_insensitive(service):
    result = service.search(RetrievalRequest(query="METHANOL"))
    experiments = _by_type(result.results, RecordType.EXPERIMENT)
    assert any(item.record_id == "exp-001" for item in experiments)


def test_fire_safety_insight_retrieval(service):
    result = service.search(RetrievalRequest(query="prevention"))
    insights = _by_type(result.results, RecordType.FIRE_SAFETY_INSIGHT)
    assert any(item.record_id == "fs-exp-001-prevention" for item in insights)
    item = next(item for item in insights if item.record_id == "fs-exp-001-prevention")
    assert item.experiment_id == "exp-001"
    assert item.evidence_category == "prevention"


def test_mission_relevance_retrieval(service):
    result = service.search(RetrievalRequest(query="Moon"))
    assessments = _by_type(result.results, RecordType.MISSION_RELEVANCE)
    assert any(item.experiment_id == "exp-001" for item in assessments)
    item = next(item for item in assessments if item.experiment_id == "exp-001")
    assert item.evidence_category == "Moon"


def test_no_invented_source_references(service):
    result = service.search(RetrievalRequest(query="methanol"))
    known = {"src-001", "src-f-001", "src-m-001", "src-hw-001"}
    for item in result.results:
        assert set(item.source_ids) <= known


def test_no_provider_needed(service):
    assert AISettings().is_configured is False
    result = service.search(RetrievalRequest(query="methanol"))
    assert result.total >= 1


def test_source_search_by_nasa_report_id(service):
    result = service.search(RetrievalRequest(query="psi-69", record_types=[RecordType.SOURCE]))
    assert result.total == 1
    assert result.results[0].record_id == "src-001"
    assert "nasa_report_id" in result.results[0].matched_fields


def test_source_verification_status_preserved(service):
    result = service.search(RetrievalRequest(query="methanol", record_types=[RecordType.SOURCE]))
    failed = next(item for item in result.results if item.record_id == "src-m-001")
    assert failed.verification_status == "verification_failed"
    assert failed.evidence_category == "dataset"
    confirmed = next(item for item in result.results if item.record_id == "src-f-001")
    assert confirmed.verification_status == "confirmed"


def test_finding_not_verified_by_confirmed_source(service):
    result = service.search(RetrievalRequest(query="flame behaviour"))
    findings = _by_type(result.results, RecordType.FINDING)
    finding = next(item for item in findings if item.record_id == "f-001")
    assert finding.source_ids == ["src-f-001"]
    assert finding.verification_status == "unverified"
    sources = _by_type(result.results, RecordType.SOURCE)
    source = next(item for item in sources if item.record_id == "src-f-001")
    assert source.verification_status == "confirmed"


def test_measurement_not_verified_by_failed_source(service):
    result = service.search(RetrievalRequest(query="thermocouple"))
    measurements = _by_type(result.results, RecordType.MEASUREMENT)
    measurement = next(item for item in measurements if item.record_id == "m-001")
    assert measurement.source_ids == ["src-m-001"]
    assert measurement.verification_status == "unverified"
    sources = service.search(RetrievalRequest(query="temperature", record_types=[RecordType.SOURCE]))
    assert sources.total == 1
    assert sources.results[0].record_id == "src-m-001"
    assert sources.results[0].verification_status == "verification_failed"


def test_source_search_case_insensitive(service):
    result = service.search(RetrievalRequest(query="METHANOL", record_types=[RecordType.SOURCE]))
    assert result.total == 2


def test_source_search_empty_when_no_match(service):
    result = service.search(RetrievalRequest(query="zzzznope", record_types=[RecordType.SOURCE]))
    assert result.total == 0
    assert result.results == []
