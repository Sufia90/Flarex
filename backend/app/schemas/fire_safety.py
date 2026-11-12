from enum import Enum

from pydantic import BaseModel, Field


class FireSafetyCategory(str, Enum):
    PREVENTION = "prevention"
    DETECTION = "detection"
    SUPPRESSION = "suppression"


class FireSafetyEvidenceStatus(str, Enum):
    DOCUMENTED = "documented"
    POTENTIAL = "potential"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceReference(BaseModel):
    record_type: str
    record_id: str
    experiment_id: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    verification_status: str | None = None


class FireSafetyInsight(BaseModel):
    insight_id: str
    category: FireSafetyCategory
    evidence_status: FireSafetyEvidenceStatus
    experiment_id: str | None = None
    experiment_name: str | None = None
    hardware_ids: list[str] = Field(default_factory=list)
    finding_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    documented_evidence: list[str] = Field(default_factory=list)
    derived_interpretation: list[str] = Field(default_factory=list)
    potential_applications: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    verification_status: str | None = None
    derived: bool = False
    methodology: str
    explanation: str


class FireSafetySummary(BaseModel):
    total_experiments: int
    total_insights: int
    prevention_count: int
    detection_count: int
    suppression_count: int
    documented_count: int
    potential_count: int
    unsupported_count: int
    unknown_count: int
    insufficient_evidence_count: int
    experiments_with_evidence: int
    experiments_without_evidence: int
    limitations: list[str] = Field(default_factory=list)
    explanation: str


class FireSafetyInsightRequest(BaseModel):
    category: FireSafetyCategory | None = None
    experiment_id: str | None = None
    hardware_id: str | None = None
    evidence_status: FireSafetyEvidenceStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
