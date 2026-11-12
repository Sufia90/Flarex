import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.schemas.experiment import Experiment
from app.schemas.hardware import Hardware
from app.schemas.relationship import ExperimentHardwareRelationship, Source
from app.services.validation import ValidationErrorItem, _is_numeric, load_json_file, validate_csv_file, validate_json_file

MODELS = {
    "experiment": Experiment,
    "hardware": Hardware,
    "relationship": ExperimentHardwareRelationship,
    "source": Source,
}


def _source_references(record, record_type):
    refs = []
    for source_id in record.get("source_ids") or []:
        refs.append(source_id)
    if record.get("source_id"):
        refs.append(record["source_id"])
    if record_type == "experiment":
        for finding in record.get("findings") or []:
            if isinstance(finding, dict) and finding.get("source_id"):
                refs.append(finding["source_id"])
        for measurement in record.get("measurements") or []:
            if isinstance(measurement, dict) and measurement.get("source_id"):
                refs.append(measurement["source_id"])
    return refs


def _measurement_errors(report, file_name):
    errors = []
    bad_ids = set()
    for record in report.valid_data:
        measurements = record.get("measurements")
        if not isinstance(measurements, list):
            continue
        for measurement in measurements:
            if not isinstance(measurement, dict):
                continue
            if _is_numeric(measurement.get("value")) and not measurement.get("unit"):
                errors.append(ValidationErrorItem(file_name=file_name, row_number=0, field="measurements.unit", value=str(record.get("id")), error="Numeric measurement requires a unit", suggestion="Add a unit, for example mm, K, or mm/s."))
                bad_ids.add(record.get("id"))
    return errors, bad_ids


def _reference_errors(report, file_name, record_type, known_source_ids, sources_name):
    errors = []
    bad_ids = set()
    for record in report.valid_data:
        for source_id in _source_references(record, record_type):
            if source_id not in known_source_ids:
                errors.append(ValidationErrorItem(file_name=file_name, row_number=0, field="source_ids", value=str(record.get("id")), error=f"Unknown source id '{source_id}' (not found in {sources_name})", suggestion="Add the source to the sources file or fix the reference."))
                bad_ids.add(record.get("id"))
    return errors, bad_ids


def _apply_errors(report, errors, bad_ids):
    if not bad_ids:
        return
    report.errors.extend(errors)
    report.valid_data = [record for record in report.valid_data if record.get("id") not in bad_ids]
    report.valid_records = len(report.valid_data)
    report.invalid_records = report.total_records - report.valid_records


def validate_file(file_path, record_type, sources_path=None):
    model = MODELS[record_type]
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        report = validate_json_file(model, file_path)
    elif suffix == ".csv":
        report = validate_csv_file(model, file_path)
    else:
        raise ValueError(f"Unsupported file type '{suffix}'. Use a .json or .csv file.")
    if record_type == "experiment":
        errors, bad_ids = _measurement_errors(report, file_path.name)
        _apply_errors(report, errors, bad_ids)
    if sources_path is not None:
        sources_data = load_json_file(sources_path)
        known_source_ids = {item.get("id") for item in sources_data if isinstance(item, dict) and item.get("id")}
        errors, bad_ids = _reference_errors(report, file_path.name, record_type, known_source_ids, sources_path.name)
        _apply_errors(report, errors, bad_ids)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a researcher data file against the FLAREX schemas. Validation only: nothing is written to the data folders.")
    parser.add_argument("file", type=Path, help="JSON or CSV file with records to validate")
    parser.add_argument("--type", required=True, choices=sorted(MODELS), help="Record type in the file")
    parser.add_argument("--sources", type=Path, default=None, help="JSON file with source records, used to check source references")
    parser.add_argument("--report", type=Path, default=None, help="Write the full validation report as JSON to this path")
    args = parser.parse_args(argv)
    if not args.file.exists():
        print(f"File not found: {args.file}")
        return 1
    if args.sources is not None and not args.sources.exists():
        print(f"Sources file not found: {args.sources}")
        return 1
    try:
        report = validate_file(args.file, args.type, args.sources)
    except (ValueError, OSError) as exc:
        print(f"Could not validate {args.file}: {exc}")
        return 1
    print(f"File: {args.file.name}")
    print(f"Total records: {report.total_records}")
    print(f"Valid records: {report.valid_records}")
    print(f"Invalid records: {report.invalid_records}")
    for error in report.errors:
        print(f"Row {error.row_number} [{error.field}]: {error.error}")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
        print(f"Report written to {args.report}")
    if report.invalid_records == 0 and not report.errors:
        print("VALID")
        return 0
    print("INVALID")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
