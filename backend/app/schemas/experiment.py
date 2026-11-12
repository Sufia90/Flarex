from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.common import BaseRecord, DataQuality, VerificationStatus


class ExperimentalConditions(BaseModel):
    fuel_material: str | None = None
    oxygen_concentration: float | None = None
    oxygen_unit: str | None = None
    oxygen_basis: str | None = None
    ambient_pressure: float | None = None
    pressure_unit: str | None = None
    temperature: float | None = None
    temperature_unit: str | None = None
    airflow_velocity: float | None = None
    airflow_unit: str | None = None
    airflow_direction: str | None = None
    gravity_condition: str | None = None
    sample_geometry: str | None = None
    sample_dimensions: str | None = None
    other_conditions: dict | None = None


class Measurement(BaseRecord):
    experiment_id: str
    test_id: str | None = None
    parameter_name: str
    parameter_description: str | None = None
    value: bool | float | str | None = None
    unit: str | None = None
    measurement_kind: Literal["measured", "derived", "interpreted"] | None = None
    original_field_name: str | None = None
    measurement_method: str | None = None
    sensor: str | None = None
    time_point: str | None = None
    source_id: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED


class Finding(BaseRecord):
    experiment_id: str
    title: str
    observation: str | None = None
    conclusion: str | None = None
    supporting_evidence: list[str] = []
    measurement_ids: list[str] = []
    limitations: list[str] = []
    fire_safety_relevance: list[Literal["prevention", "detection", "suppression"]] = Field(default_factory=list)
    source_id: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED


class Experiment(BaseRecord):
    nasa_investigation_id: str | None = None
    name: str
    acronym: str | None = None
    description: str | None = None
    scientific_objective: str | None = None
    research_category: str | None = None
    combustion_type: str | None = None
    fuel_material: str | None = None
    sample_geometry: str | None = None
    sample_dimensions: str | None = None
    hardware_ids: list[str] = []
    related_investigation_ids: list[str] = []
    conditions: ExperimentalConditions | None = None
    measurements: list[Measurement] = []
    findings: list[Finding] = []
    limitations: list[str] = []
    source_ids: list[str] = []
    media_ids: list[str] = []
    mission_applicability: list[Literal["ISS", "Moon", "Mars"]] = Field(default_factory=list)
    transferability_note: str | None = None
    fire_safety_relevance: list[Literal["prevention", "detection", "suppression"]] = Field(default_factory=list)
    data_quality: DataQuality = DataQuality()
