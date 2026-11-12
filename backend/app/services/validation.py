import csv
import json
from pathlib import Path
from pydantic import BaseModel, ValidationError
from app.schemas.common import DataCompleteness, DataQuality
from app.schemas.experiment import Experiment, Measurement


class ValidationErrorItem(BaseModel):
    file_name: str
    row_number: int
    field: str
    value: str | None = None
    error: str
    suggestion: str | None = None


class ValidationReport(BaseModel):
    file_name: str
    total_records: int
    valid_records: int
    invalid_records: int
    errors: list[ValidationErrorItem] = []
    valid_data: list[dict] = []


def load_json_file(file_path):
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return [data]


def load_csv_file(file_path):
    with open(file_path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _is_numeric(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


def validate_records(model, records, file_name, first_row=1):
    errors = []
    valid_data = []
    seen_ids = set()
    for index, record in enumerate(records, start=first_row):
        record_id = record.get("id")
        if record_id and record_id in seen_ids:
            errors.append(ValidationErrorItem(file_name=file_name, row_number=index, field="id", value=str(record_id), error=f"Duplicate id '{record_id}'", suggestion="Use a unique id for each record."))
            continue
        seen_ids.add(record_id)
        try:
            item = model(**record)
        except ValidationError as e:
            for err in e.errors():
                field = str(err["loc"][0]) if err["loc"] else "unknown"
                errors.append(ValidationErrorItem(file_name=file_name, row_number=index, field=field, value=str(record.get(field)), error=err["msg"], suggestion=f"Provide a valid value for '{field}'."))
            continue
        if isinstance(item, Measurement) and _is_numeric(item.value) and not item.unit:
            errors.append(ValidationErrorItem(file_name=file_name, row_number=index, field="unit", value=None, error="Numeric measurement requires a unit", suggestion="Add a unit, for example mm, K, or mm/s."))
            continue
        valid_data.append(item.model_dump(mode="json"))
    return ValidationReport(file_name=file_name, total_records=len(records), valid_records=len(valid_data), invalid_records=len(records) - len(valid_data), errors=errors, valid_data=valid_data)


def validate_json_file(model, file_path):
    records = load_json_file(file_path)
    return validate_records(model, records, file_name=Path(file_path).name, first_row=1)


def validate_csv_file(model, file_path):
    records = load_csv_file(file_path)
    return validate_records(model, records, file_name=Path(file_path).name, first_row=2)


def compute_data_quality(experiment):
    checks = {"description": experiment.description, "scientific_objective": experiment.scientific_objective, "research_category": experiment.research_category, "conditions": experiment.conditions, "source_ids": experiment.source_ids, "measurements": experiment.measurements, "findings": experiment.findings}
    present = sum(1 for c in checks.values() if c)
    missing_fields = [name for name, value in checks.items() if not value]
    if present == len(checks):
        completeness = DataCompleteness.COMPLETE
    elif present == 0:
        completeness = DataCompleteness.INCOMPLETE
    else:
        completeness = DataCompleteness.PARTIALLY_COMPLETE
    return DataQuality(completeness=completeness, verification_status=experiment.data_quality.verification_status, missing_fields=missing_fields, notes=experiment.data_quality.notes)
