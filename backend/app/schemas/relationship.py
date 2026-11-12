from enum import Enum
from pydantic import BaseModel, field_validator, model_validator
from .common import BaseRecord, VerificationStatus


class RelationshipType(str, Enum):
    USED_IN = "used_in"
    HOUSED_IN = "housed_in"
    PART_OF = "part_of"
    SUPPORTS = "supports"
    PRODUCED_BY = "produced_by"


class ExperimentHardwareRelationship(BaseRecord):
    experiment_id: str
    hardware_id: str
    relationship_type: RelationshipType = RelationshipType.USED_IN
    role: str | None = None
    evidence: str | None = None
    source_id: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    notes: str | None = None

    @model_validator(mode="after")
    def check_ids_differ(self):
        if self.experiment_id == self.hardware_id:
            raise ValueError("experiment_id and hardware_id must be different")
        return self


class SourceType(str, Enum):
    NASA_REPORT = "nasa_report"
    PAPER = "paper"
    DATASET = "dataset"
    WEBSITE = "website"
    OTHER = "other"


class Source(BaseRecord):
    source_type: SourceType = SourceType.OTHER
    title: str
    nasa_report_id: str | None = None
    doi: str | None = None
    url: str | None = None
    publisher: str | None = None
    publication_date: str | None = None
    access_date: str | None = None
    page_section: str | None = None
    description: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    @field_validator("doi")
    @classmethod
    def check_doi(cls, v):
        if v is not None and not v.startswith("10."):
            raise ValueError("DOI must start with 10.")
        return v

    @field_validator("url")
    @classmethod
    def check_url(cls, v):
        if v is not None and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class MediaReference(BaseRecord):
    file_path: str | None = None
    external_url: str | None = None
    media_type: str | None = None
    caption: str | None = None
    description: str | None = None
    experiment_id: str | None = None
    hardware_id: str | None = None
    original_source_url: str | None = None
    credit: str | None = None
    license: str | None = None
