import json
from pathlib import Path
from app.repositories.experiment_repository import ExperimentRepository
from app.schemas.experiment import Experiment


def _payload(experiment_id="exp-001", name="Synthetic FLEX Test"):
    return {"id": experiment_id, "name": name}


def _write_json(directory: Path, filename: str, records) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    file = directory / filename
    file.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return file


def test_invalid_record_is_skipped_but_reported(tmp_path):
    experiments_dir = tmp_path / "experiments"
    bad = {"id": "exp-bad"}
    file = _write_json(experiments_dir, "experiments.json", [_payload(), bad])
    before = file.read_text(encoding="utf-8")
    repository = ExperimentRepository(data_dir=experiments_dir)
    assert len(repository.get_all()) == 1
    invalid = repository.get_invalid_records()
    assert len(invalid) == 1
    assert invalid[0]["record_id"] == "exp-bad"
    assert invalid[0]["record"] == bad
    assert "name" in invalid[0]["error"]
    assert file.read_text(encoding="utf-8") == before


def test_invalid_record_survives_update(tmp_path):
    experiments_dir = tmp_path / "experiments"
    bad = {"id": "exp-bad"}
    file = _write_json(experiments_dir, "experiments.json", [_payload(), bad])
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.update("exp-001", Experiment(id="exp-001", name="Updated Synthetic FLEX Test"))
    records = json.loads(file.read_text(encoding="utf-8"))
    ids = [record.get("id") for record in records]
    assert "exp-bad" in ids
    assert "exp-001" in ids
    assert repository.get_by_id("exp-001").name == "Updated Synthetic FLEX Test"


def test_invalid_record_survives_delete(tmp_path):
    experiments_dir = tmp_path / "experiments"
    bad = {"id": "exp-bad"}
    file = _write_json(experiments_dir, "experiments.json", [_payload(), bad, _payload("exp-002", "Synthetic ACME Test")])
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.delete("exp-001")
    records = json.loads(file.read_text(encoding="utf-8"))
    ids = [record.get("id") for record in records]
    assert "exp-bad" in ids
    assert "exp-001" not in ids
    assert "exp-002" in ids


def test_invalid_record_survives_create(tmp_path):
    experiments_dir = tmp_path / "experiments"
    bad = {"id": "exp-bad"}
    file = _write_json(experiments_dir, "experiments.json", [_payload(), bad])
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.create(Experiment(id="exp-002", name="Synthetic ACME Test"))
    records = json.loads(file.read_text(encoding="utf-8"))
    ids = [record.get("id") for record in records]
    assert "exp-bad" in ids
    assert "exp-001" in ids
    assert "exp-002" in ids


def test_malformed_file_is_not_destroyed_by_create(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    malformed = experiments_dir / "other.json"
    malformed.write_text("{ not json", encoding="utf-8")
    before = malformed.read_text(encoding="utf-8")
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.create(Experiment(id="exp-001", name="Synthetic FLEX Test"))
    assert malformed.read_text(encoding="utf-8") == before
    assert len(repository.get_invalid_records()) == 1


def test_duplicate_id_is_reported_as_invalid(tmp_path):
    experiments_dir = tmp_path / "experiments"
    _write_json(experiments_dir, "experiments.json", [_payload()])
    _write_json(experiments_dir, "other.json", [_payload("exp-001", "Duplicate Synthetic FLEX Test")])
    repository = ExperimentRepository(data_dir=experiments_dir)
    assert len(repository.get_all()) == 1
    assert repository.get_by_id("exp-001").name == "Synthetic FLEX Test"
    invalid = repository.get_invalid_records()
    assert len(invalid) == 1
    assert invalid[0]["record_id"] == "exp-001"
    assert "duplicate" in invalid[0]["error"]


def test_valid_records_stay_editable_after_fix(tmp_path):
    experiments_dir = tmp_path / "experiments"
    _write_json(experiments_dir, "experiments.json", [_payload()])
    repository = ExperimentRepository(data_dir=experiments_dir)
    updated = repository.update("exp-001", Experiment(id="exp-001", name="Updated Synthetic FLEX Test"))
    assert updated.name == "Updated Synthetic FLEX Test"
    fresh = ExperimentRepository(data_dir=experiments_dir)
    assert fresh.get_by_id("exp-001").name == "Updated Synthetic FLEX Test"
