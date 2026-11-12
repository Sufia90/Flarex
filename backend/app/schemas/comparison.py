from enum import Enum
from pydantic import BaseModel, Field


class ComparabilityStatus(str, Enum):
    COMPARABLE = "comparable"
    PARTIALLY_COMPARABLE = "partially_comparable"
    NOT_COMPARABLE = "not_comparable"
    INSUFFICIENT_DATA = "insufficient_data"


class ComparisonCategory(str, Enum):
    EXPERIMENT = "experiment"
    HARDWARE = "hardware"
    MEASUREMENT = "measurement"
    FUEL_MATERIAL = "fuel_material"
    OXYGEN_CONDITION = "oxygen_condition"
    PRESSURE_CONDITION = "pressure_condition"
    TEMPERATURE_CONDITION = "temperature_condition"
    AIRFLOW_CONDITION = "airflow_condition"
    GRAVITY_CONDITION = "gravity_condition"


class ComparedValue(BaseModel):
    item_id: str
    value: bool | float | str | None = None
    unit: str | None = None
    measurement_kind: str | None = None
    measurement_method: str | None = None
    sensor: str | None = None
    time_point: str | None = None
    source_id: str | None = None
    verification_status: str | None = None
    missing_reason: str | None = None


class ParameterComparison(BaseModel):
    parameter_name: str
    category: ComparisonCategory
    status: ComparabilityStatus
    reason: str
    values: list[ComparedValue] = []
    units: list[str] = []
    conditions_note: str | None = None


class ConditionComparison(BaseModel):
    condition_name: str
    status: ComparabilityStatus
    reason: str
    values: list[ComparedValue] = []


class ExperimentComparison(BaseModel):
    comparison_id: str | None = None
    category: ComparisonCategory = ComparisonCategory.EXPERIMENT
    experiment_ids: list[str]
    parameters: list[ParameterComparison] = []
    conditions: list[ConditionComparison] = []
    similarities: list[str] = []
    differences: list[str] = []
    missing_information: list[str] = []
    incompatible_items: list[str] = []
    source_ids: list[str] = []
    explanation: str
    limitations: list[str] = []
    methodology: str


class HardwareComparison(BaseModel):
    comparison_id: str | None = None
    category: ComparisonCategory = ComparisonCategory.HARDWARE
    hardware_ids: list[str]
    hardware_types: list[str] = []
    same_hardware_type: bool = True
    fields: list[ParameterComparison] = []
    shared_measurements: list[str] = []
    unique_measurements: dict[str, list[str]] = {}
    similarities: list[str] = []
    differences: list[str] = []
    missing_information: list[str] = []
    source_ids: list[str] = []
    explanation: str
    limitations: list[str] = []
    methodology: str


class MeasurementComparison(BaseModel):
    comparison_id: str | None = None
    category: ComparisonCategory = ComparisonCategory.MEASUREMENT
    measurement_ids: list[str]
    parameters: list[ParameterComparison] = []
    similarities: list[str] = []
    differences: list[str] = []
    missing_information: list[str] = []
    incompatible_items: list[str] = []
    source_ids: list[str] = []
    explanation: str
    limitations: list[str] = []
    methodology: str


class ExperimentComparisonRequest(BaseModel):
    experiment_ids: list[str] = Field(min_length=2, max_length=10)
    parameters: list[str] | None = None
    include_conditions: bool = True


class HardwareComparisonRequest(BaseModel):
    hardware_ids: list[str] = Field(min_length=2, max_length=10)
    fields: list[str] | None = None


class MeasurementComparisonRequest(BaseModel):
    measurement_ids: list[str] = Field(min_length=2, max_length=10)
    parameter_names: list[str] | None = None
