import json
from app.schemas.experiment import Experiment, Measurement
from app.services.validation import load_csv_file, load_json_file, validate_csv_file, validate_json_file, validate_records


def test_valid_json_loading(tmp_path):
    data = [{"id": "synthetic-exp-001", "name": "Synthetic JSON example"}, {"id": "synthetic-exp-002", "name": "Synthetic JSON example 2"}]
    p = tmp_path / "synthetic_experiments.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    loaded = load_json_file(p)
    assert len(loaded) == 2
    report = validate_json_file(Experiment, p)
    assert report.total_records == 2
    assert report.valid_records == 2
    assert report.invalid_records == 0
    assert report.errors == []


def test_valid_csv_loading(tmp_path):
    p = tmp_path / "synthetic_measurements.csv"
    p.write_text("id,experiment_id,parameter_name,value,unit\nsynthetic-m-001,synthetic-exp-001,flame diameter,5.0,mm\nsynthetic-m-002,synthetic-exp-001,outcome,extinction,\n", encoding="utf-8")
    loaded = load_csv_file(p)
    assert len(loaded) == 2
    report = validate_csv_file(Measurement, p)
    assert report.valid_records == 2
    assert report.invalid_records == 0


def test_invalid_csv_records(tmp_path):
    p = tmp_path / "synthetic_bad.csv"
    p.write_text("id,experiment_id,parameter_name,value,unit\nsynthetic-m-001,synthetic-exp-001,flame diameter,5.0,mm\nsynthetic-m-002,synthetic-exp-001,flame temperature,100.0,\nsynthetic-m-001,synthetic-exp-001,flame diameter,6.0,mm\n", encoding="utf-8")
    report = validate_csv_file(Measurement, p)
    assert report.total_records == 3
    assert report.valid_records == 1
    assert report.invalid_records == 2
    assert any(e.field == "unit" for e in report.errors)
    assert any(e.field == "id" and "Duplicate" in e.error for e in report.errors)


def test_duplicate_identifiers():
    report = validate_records(Experiment, [{"id": "synthetic-exp-001", "name": "One"}, {"id": "synthetic-exp-001", "name": "Two"}], file_name="synthetic.json")
    assert report.valid_records == 1
    assert report.invalid_records == 1
    assert report.errors[0].field == "id"


def test_invalid_experiment_missing_name():
    report = validate_records(Experiment, [{"id": "synthetic-exp-009"}], file_name="synthetic.json")
    assert report.invalid_records == 1
    assert report.errors[0].field == "name"
    assert report.errors[0].file_name == "synthetic.json"
    assert report.errors[0].row_number == 1
    assert report.errors[0].suggestion is not None


def test_numeric_measurement_without_unit_flagged():
    report = validate_records(Measurement, [{"id": "synthetic-m-010", "experiment_id": "synthetic-exp-001", "parameter_name": "flame temperature", "value": 100.0}], file_name="synthetic.json")
    assert report.invalid_records == 1
    assert report.errors[0].field == "unit"


def test_zero_measurement_not_flagged_as_missing():
    report = validate_records(Measurement, [{"id": "synthetic-m-011", "experiment_id": "synthetic-exp-001", "parameter_name": "burning rate", "value": 0.0, "unit": "mm/s"}], file_name="synthetic.json")
    assert report.valid_records == 1


def test_validate_records_keeps_original_data_unchanged():
    records = [{"id": "synthetic-exp-001", "name": "Synthetic"}]
    report = validate_records(Experiment, records, file_name="synthetic.json")
    assert records[0] == {"id": "synthetic-exp-001", "name": "Synthetic"}
    assert report.valid_data[0]["id"] == "synthetic-exp-001"
