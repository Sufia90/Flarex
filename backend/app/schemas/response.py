from pydantic import BaseModel
from app.schemas.experiment import Experiment
from app.schemas.fire_safety import FireSafetyInsight
from app.schemas.hardware import Hardware
from app.schemas.relationship import ExperimentHardwareRelationship, Source


class PaginatedExperimentList(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[Experiment]


class PaginatedHardwareList(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[Hardware]


class PaginatedRelationshipList(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[ExperimentHardwareRelationship]


class PaginatedFireSafetyInsightList(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[FireSafetyInsight]


class PaginatedSourceList(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[Source]


class DeleteResponse(BaseModel):
    message: str
    deleted_id: str


class ErrorResponse(BaseModel):
    detail: str
