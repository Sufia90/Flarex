import pytest
from pydantic import ValidationError

from app.ai import AISettings, NoProviderAssistant, ResearchAssistant, RetrievalService, SAFETY_RULES, evaluate_retrieval
from app.ai.config import get_ai_settings
from app.schemas.retrieval import AssistantRequest, EvaluationRecord, GroundingStatus, RecordType, RetrievalResult


def _result(record_id, source_ids=None):
    return RetrievalResult(
        record_type=RecordType.EXPERIMENT,
        record_id=record_id,
        title="Synthetic",
        text="Methanol test.",
        experiment_id="exp-001",
        source_ids=source_ids or ["src-001"],
        verification_status="unverified",
    )


def test_no_provider_configuration():
    settings = AISettings()
    assert settings.provider is None
    assert settings.api_key is None
    assert settings.enabled is False
    assert settings.is_configured is False
    assert get_ai_settings().is_configured is False


def test_missing_api_key():
    settings = AISettings(provider="gemini", api_key=None)
    assert settings.is_configured is False
    settings = AISettings(provider=None, api_key="some-key")
    assert settings.is_configured is False


def test_no_external_api_call_required():
    assistant = NoProviderAssistant()
    response = assistant.answer(AssistantRequest(question="What is FLEX?"), [])
    assert response.grounding_status == GroundingStatus.NO_EVIDENCE
    assert "No relevant evidence was found" in response.answer
    assert "No external model call was made" in " ".join(response.limitations)


def test_assistant_rejects_empty_evidence():
    assistant = NoProviderAssistant()
    response = assistant.answer(AssistantRequest(question="What is FLEX?"), [])
    assert response.evidence == []
    assert response.source_ids == []
    assert response.grounding_status == GroundingStatus.NO_EVIDENCE
    assert "No relevant evidence was found" in response.answer


def test_assistant_flags_evidence_without_provider():
    assistant = NoProviderAssistant()
    evidence = [_result("exp-001")]
    response = assistant.answer(AssistantRequest(question="What is FLEX?"), evidence)
    assert response.grounding_status == GroundingStatus.INSUFFICIENT_EVIDENCE
    assert response.evidence == evidence
    assert response.source_ids == ["src-001"]
    assert "No AI provider is configured" in response.answer
    assert "not an answer by itself" in " ".join(response.warnings)


def test_assistant_interface_is_abstract():
    with pytest.raises(TypeError):
        ResearchAssistant()
    assert isinstance(NoProviderAssistant(), ResearchAssistant)


def test_safety_rules_present():
    assert len(SAFETY_RULES) == 10
    assert any("Never invent citations" in rule for rule in SAFETY_RULES)
    assert any("Never provide unsupported emergency instructions" in rule for rule in SAFETY_RULES)
    assert any("Never claim that an experiment proves universal fire safety" in rule for rule in SAFETY_RULES)


def test_evaluation_record_validation():
    record = EvaluationRecord(
        evaluation_id="eval-001",
        question="What is FLEX?",
        expected_evidence_ids=["exp-001"],
        retrieved_evidence_ids=["exp-001"],
        grounding_status=GroundingStatus.GROUNDED,
    )
    assert record.evaluation_id == "eval-001"
    with pytest.raises(ValidationError):
        EvaluationRecord(
            evaluation_id="eval-002",
            question="What is FLEX?",
            source_coverage=1.5,
            grounding_status=GroundingStatus.GROUNDED,
        )
    with pytest.raises(ValidationError):
        EvaluationRecord(
            evaluation_id="eval-003",
            question="What is FLEX?",
            source_coverage=-0.1,
            grounding_status=GroundingStatus.GROUNDED,
        )


def test_evaluation_grounded():
    record = EvaluationRecord(
        evaluation_id="eval-001",
        question="What is FLEX?",
        expected_evidence_ids=["a", "b"],
        retrieved_evidence_ids=["a", "b"],
        grounding_status=GroundingStatus.NO_EVIDENCE,
    )
    result = evaluate_retrieval(record)
    assert result.source_coverage == 1.0
    assert result.grounding_status == GroundingStatus.GROUNDED
    assert result.missing_evidence == []


def test_evaluation_partial():
    record = EvaluationRecord(
        evaluation_id="eval-001",
        question="What is FLEX?",
        expected_evidence_ids=["a", "b", "c"],
        retrieved_evidence_ids=["a"],
        grounding_status=GroundingStatus.NO_EVIDENCE,
    )
    result = evaluate_retrieval(record)
    assert result.source_coverage == pytest.approx(1 / 3)
    assert result.grounding_status == GroundingStatus.INSUFFICIENT_EVIDENCE
    assert result.missing_evidence == ["b", "c"]


def test_evaluation_no_evidence():
    record = EvaluationRecord(
        evaluation_id="eval-001",
        question="What is FLEX?",
        expected_evidence_ids=["a"],
        retrieved_evidence_ids=[],
        grounding_status=GroundingStatus.GROUNDED,
    )
    result = evaluate_retrieval(record)
    assert result.source_coverage == 0.0
    assert result.grounding_status == GroundingStatus.NO_EVIDENCE
    assert result.missing_evidence == ["a"]


def test_evaluation_no_expected():
    record = EvaluationRecord(
        evaluation_id="eval-001",
        question="What is FLEX?",
        expected_evidence_ids=[],
        retrieved_evidence_ids=["a"],
        grounding_status=GroundingStatus.NO_EVIDENCE,
    )
    result = evaluate_retrieval(record)
    assert result.source_coverage is None
    assert result.grounding_status == GroundingStatus.GROUNDED
    assert result.missing_evidence == []


def test_no_invented_source_references():
    assistant = NoProviderAssistant()
    evidence = [_result("exp-001", ["src-001"]), _result("exp-002", ["src-002"])]
    response = assistant.answer(AssistantRequest(question="What is FLEX?"), evidence)
    assert response.source_ids == ["src-001", "src-002"]
    assert set(response.source_ids) <= {"src-001", "src-002"}


def test_assistant_request_defaults():
    request = AssistantRequest(question="What is FLEX?")
    assert request.evidence_only is True
    assert request.max_results == 5
    with pytest.raises(ValidationError):
        AssistantRequest(question="")


def test_ai_package_exports():
    assert AISettings is not None
    assert RetrievalService is not None
    assert NoProviderAssistant is not None
    assert evaluate_retrieval is not None
