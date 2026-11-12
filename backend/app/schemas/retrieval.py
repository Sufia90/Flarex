from enum import Enum

from pydantic import BaseModel, Field


class RecordType(str, Enum):
    EXPERIMENT = "experiment"
    FINDING = "finding"
    MEASUREMENT = "measurement"
    HARDWARE = "hardware"
    RELATIONSHIP = "relationship"
    SOURCE = "source"
    FIRE_SAFETY_INSIGHT = "fire_safety_insight"
    MISSION_RELEVANCE = "mission_relevance"


class GroundingStatus(str, Enum):
    GROUNDED = "grounded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NO_EVIDENCE = "no_evidence"


class RetrievalResult(BaseModel):
    record_type: RecordType
    record_id: str
    title: str | None = None
    text: str | None = None
    experiment_id: str | None = None
    hardware_id: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    verification_status: str | None = None
    evidence_category: str | None = None
    limitations: list[str] = Field(default_factory=list)
    matched_fields: list[str] = Field(default_factory=list)


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1)
    record_types: list[RecordType] | None = None
    experiment_id: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class RetrievalResponse(BaseModel):
    query: str
    total: int
    results: list[RetrievalResult] = Field(default_factory=list)
    methodology: str
    explanation: str
    limitations: list[str] = Field(default_factory=list)


class AssistantRequest(BaseModel):
    question: str = Field(min_length=1)
    max_results: int = Field(default=5, ge=1, le=20)
    evidence_only: bool = True


class AssistantResponse(BaseModel):
    answer: str
    evidence: list[RetrievalResult] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    grounding_status: GroundingStatus
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class EvaluationRecord(BaseModel):
    evaluation_id: str
    question: str = Field(min_length=1)
    expected_evidence_ids: list[str] = Field(default_factory=list)
    retrieved_evidence_ids: list[str] = Field(default_factory=list)
    source_coverage: float | None = Field(default=None, ge=0, le=1)
    grounding_status: GroundingStatus
    missing_evidence: list[str] = Field(default_factory=list)
    evaluation_notes: str | None = None
