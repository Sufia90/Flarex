from enum import Enum
from pydantic import BaseModel


class MissionContext(str, Enum):
    ISS = "ISS"
    MOON = "Moon"
    MARS = "Mars"


class RelevanceLevel(str, Enum):
    DOCUMENTED = "documented"
    POTENTIAL = "potential"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class MissionRelevanceAssessment(BaseModel):
    assessment_id: str | None = None
    subject_type: str
    subject_id: str
    subject_name: str | None = None
    mission: MissionContext
    relevance_level: RelevanceLevel
    relevant_conditions: list[str] = []
    similarities: list[str] = []
    differences: list[str] = []
    supporting_evidence: list[str] = []
    transferability_limitations: list[str] = []
    missing_information: list[str] = []
    source_ids: list[str] = []
    evidence_status: str | None = None
    derived_from_experiment_ids: list[str] = []
    explanation: str
    limitations: list[str] = []
    methodology: str
