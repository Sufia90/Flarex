from enum import Enum
from .common import BaseRecord, DataQuality


class HardwareType(str, Enum):
    FACILITY = "facility"
    APPARATUS = "apparatus"
    COMPONENT = "component"
    INSTRUMENT = "instrument"


class Hardware(BaseRecord):
    name: str
    acronym: str | None = None
    hardware_type: HardwareType
    description: str | None = None
    purpose: str | None = None
    facility_classification: str | None = None
    parent_hardware_id: str | None = None
    component_ids: list[str] = []
    image_ids: list[str] = []
    diagram_ids: list[str] = []
    supported_measurements: list[str] = []
    related_experiment_ids: list[str] = []
    source_ids: list[str] = []
    limitations: str | None = None
    data_quality: DataQuality = DataQuality()
