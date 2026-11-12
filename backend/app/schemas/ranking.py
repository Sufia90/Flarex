from enum import Enum
from pydantic import BaseModel, Field


class RankingCriterion(str, Enum):
    HARDWARE_EXPERIMENT_ASSOCIATIONS = "hardware_experiment_associations"
    EXPERIMENT_DOCUMENTATION_COMPLETENESS = "experiment_documentation_completeness"
    EXPERIMENT_MEASUREMENT_COVERAGE = "experiment_measurement_coverage"


class RankingStatus(str, Enum):
    RANKED = "ranked"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RankingItem(BaseModel):
    rank: int | None = None
    item_id: str
    item_name: str | None = None
    metric_value: int | float
    metric_max: int | None = None
    metric_breakdown: dict[str, int] = {}
    evidence_ids: list[str] = []
    data_completeness: str | None = None
    verification_status: str | None = None
    explanation: str
    limitations: list[str] = []


class RankingResult(BaseModel):
    ranking_id: str | None = None
    criterion: RankingCriterion
    title: str
    question: str
    methodology: str
    metric_name: str
    metric_description: str
    metric_max: int | None = None
    status: RankingStatus
    eligible_item_ids: list[str] = []
    items: list[RankingItem] = []
    source_ids: list[str] = []
    explanation: str
    limitations: list[str] = []


class RankingRequest(BaseModel):
    criterion: RankingCriterion
    item_ids: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=50)
