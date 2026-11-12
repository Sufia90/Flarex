from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class VerificationStatus(str, Enum):
    CONFIRMED = "confirmed"
    PARTIALLY_DOCUMENTED = "partially_documented"
    UNVERIFIED = "unverified"
    VERIFICATION_FAILED = "verification_failed"


class DataCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIALLY_COMPLETE = "partially_complete"
    INCOMPLETE = "incomplete"
    NOT_YET_VERIFIED = "not_yet_verified"


class MissingValue(str, Enum):
    MISSING = "missing"
    UNKNOWN = "unknown"
    NOT_REPORTED = "not_reported"
    NOT_APPLICABLE = "not_applicable"


class BaseRecord(BaseModel):
    id: str
    schema_version: str = "1.0"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str = "active"


class DataQuality(BaseModel):
    completeness: DataCompleteness = DataCompleteness.NOT_YET_VERIFIED
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    missing_fields: list[str] = []
    notes: str | None = None
