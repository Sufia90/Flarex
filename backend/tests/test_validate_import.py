import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_import.py"


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *[str(a) for a in args]], capture_output=True, text=True, timeout=120)


def write_json(tmp_path, name, records):
    path = tmp_path / name
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def test_valid_experiments_file_passes(tmp_path):
    path = write_json(tmp_path, "experiments.json", [{"id": "exp-001", "name": "Synthetic FLEX test"}])
    result = run_cli(path, "--type", "experiment")
    assert result.returncode == 0
    assert "VALID" in result.stdout
    assert "Valid records: 1" in result.stdout


def test_invalid_record_fails(tmp_path):
    path = write_json(tmp_path, "experiments.json", [{"id": "exp-001"}])
    result = run_cli(path, "--type", "experiment")
    assert result.returncode == 1
    assert "INVALID" in result.stdout
    assert "Invalid records: 1" in result.stdout


def test_duplicate_ids_fail(tmp_path):
    path = write_json(tmp_path, "experiments.json", [{"id": "exp-001", "name": "First"}, {"id": "exp-001", "name": "Second"}])
    result = run_cli(path, "--type", "experiment")
    assert result.returncode == 1
    assert "Duplicate id" in result.stdout


def test_numeric_measurement_without_unit_fails(tmp_path):
    record = {"id": "exp-001", "name": "Synthetic FLEX test", "measurements": [{"id": "m-001", "experiment_id": "exp-001", "parameter_name": "flame temperature", "value": 1200.0, "unit": None}]}
    path = write_json(tmp_path, "experiments.json", [record])
    result = run_cli(path, "--type", "experiment")
    assert result.returncode == 1
    assert "Numeric measurement requires a unit" in result.stdout


def test_unknown_source_reference_fails_when_sources_given(tmp_path):
    experiments = write_json(tmp_path, "experiments.json", [{"id": "exp-001", "name": "Synthetic FLEX test", "source_ids": ["src-missing"]}])
    sources = write_json(tmp_path, "sources.json", [{"id": "src-001", "title": "FLEX Experiment Overview"}])
    result = run_cli(experiments, "--type", "experiment", "--sources", sources)
    assert result.returncode == 1
    assert "Unknown source id 'src-missing'" in result.stdout


def test_known_source_reference_passes(tmp_path):
    experiments = write_json(tmp_path, "experiments.json", [{"id": "exp-001", "name": "Synthetic FLEX test", "source_ids": ["src-001"]}])
    sources = write_json(tmp_path, "sources.json", [{"id": "src-001", "title": "FLEX Experiment Overview"}])
    result = run_cli(experiments, "--type", "experiment", "--sources", sources)
    assert result.returncode == 0
    assert "VALID" in result.stdout


def test_missing_file_fails(tmp_path):
    result = run_cli(tmp_path / "no-such-file.json", "--type", "experiment")
    assert result.returncode == 1
    assert "not found" in result.stdout.lower()


def test_report_file_written(tmp_path):
    path = write_json(tmp_path, "experiments.json", [{"id": "exp-001", "name": "Synthetic FLEX test"}])
    report_path = tmp_path / "report.json"
    result = run_cli(path, "--type", "experiment", "--report", report_path)
    assert result.returncode == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["total_records"] == 1
    assert report["valid_records"] == 1
    assert report["invalid_records"] == 0


def test_csv_file_validated(tmp_path):
    path = tmp_path / "experiments.csv"
    path.write_text("id,name\nexp-001,Synthetic FLEX test\n", encoding="utf-8")
    result = run_cli(path, "--type", "experiment")
    assert result.returncode == 0
    assert "VALID" in result.stdout
