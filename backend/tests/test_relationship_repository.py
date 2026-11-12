import json
import pytest
from pathlib import Path
from app.repositories.relationship_repository import DuplicateRelationshipError, DuplicateRelationshipReferenceError, RelationshipNotFoundError, RelationshipRepository
from app.schemas.relationship import ExperimentHardwareRelationship


def _payload(relationship_id="rel-001", experiment_id="exp-001", hardware_id="hw-cir", **overrides):
    payload = {
        "id": relationship_id,
        "experiment_id": experiment_id,
        "hardware_id": hardware_id,
        "relationship_type": "used_in",
        "role": "Synthetic role for testing only",
        "evidence": "Synthetic evidence for testing only",
        "source_id": "src-001",
        "verification_status": "unverified",
        "notes": "Synthetic note for testing only",
    }
    payload.update(overrides)
    return payload


def _write_json(directory: Path, filename: str, records) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    file = directory / filename
    file.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return file


def test_empty_folder_returns_empty_list(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert repository.get_all() == []
    assert repository.get_invalid_records() == []


def test_missing_folder_returns_empty_list(tmp_path):
    repository = RelationshipRepository(data_dir=tmp_path / "relationships")
    assert repository.get_all() == []


def test_load_valid_relationship_records(tmp_path):
    relationships_dir = tmp_path / "relationships"
    _write_json(relationships_dir, "experiment_hardware.json", [_payload(), _payload("rel-002", "exp-002", "hw-msg")])
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert len(repository.get_all()) == 2
    assert repository.get_all()[0].experiment_id == "exp-001"


def test_get_by_id(tmp_path):
    relationships_dir = tmp_path / "relationships"
    _write_json(relationships_dir, "experiment_hardware.json", [_payload()])
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert repository.get_by_id("rel-001").hardware_id == "hw-cir"
    assert repository.get_by_id("rel-no-such") is None


def test_get_by_experiment_id(tmp_path):
    relationships_dir = tmp_path / "relationships"
    _write_json(relationships_dir, "experiment_hardware.json", [_payload("rel-001", "exp-001", "hw-cir"), _payload("rel-002", "exp-001", "hw-msg"), _payload("rel-003", "exp-002", "hw-cir", relationship_type="housed_in")])
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert len(repository.get_by_experiment_id("exp-001")) == 2
    assert len(repository.get_by_experiment_id("exp-002")) == 1
    assert repository.get_by_experiment_id("exp-no-such") == []


def test_get_by_hardware_id(tmp_path):
    relationships_dir = tmp_path / "relationships"
    _write_json(relationships_dir, "experiment_hardware.json", [_payload("rel-001", "exp-001", "hw-cir"), _payload("rel-002", "exp-002", "hw-cir", relationship_type="housed_in"), _payload("rel-003", "exp-001", "hw-msg")])
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert len(repository.get_by_hardware_id("hw-cir")) == 2
    assert len(repository.get_by_hardware_id("hw-msg")) == 1
    assert repository.get_by_hardware_id("hw-no-such") == []


def test_create_relationship_saves_to_store_file(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    created = repository.create(ExperimentHardwareRelationship(**_payload()))
    assert created.id == "rel-001"
    assert len(repository.get_all()) == 1
    assert (relationships_dir / "experiment_hardware.json").is_file()
    fresh = RelationshipRepository(data_dir=relationships_dir)
    assert len(fresh.get_all()) == 1
    assert fresh.get_by_id("rel-001").hardware_id == "hw-cir"


def test_create_duplicate_id_is_rejected(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload()))
    with pytest.raises(DuplicateRelationshipError):
        repository.create(ExperimentHardwareRelationship(**_payload("rel-001", "exp-002", "hw-msg")))
    assert len(repository.get_all()) == 1


def test_create_duplicate_link_is_rejected(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload()))
    with pytest.raises(DuplicateRelationshipReferenceError):
        repository.create(ExperimentHardwareRelationship(**_payload("rel-002", "exp-001", "hw-cir")))
    assert len(repository.get_all()) == 1


def test_create_same_pair_different_type_is_allowed(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload()))
    created = repository.create(ExperimentHardwareRelationship(**_payload("rel-002", "exp-001", "hw-cir", relationship_type="housed_in")))
    assert created.relationship_type.value == "housed_in"
    assert len(repository.get_all()) == 2


def test_update_relationship_preserves_other_records(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload("rel-001", "exp-001", "hw-cir")))
    repository.create(ExperimentHardwareRelationship(**_payload("rel-002", "exp-002", "hw-msg")))
    updated = repository.update("rel-001", ExperimentHardwareRelationship(**_payload("rel-001", "exp-001", "hw-cir", role="Updated synthetic role")))
    assert updated.role == "Updated synthetic role"
    assert len(repository.get_all()) == 2
    assert repository.get_by_id("rel-002").role == "Synthetic role for testing only"


def test_update_nonexistent_raises_not_found(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    with pytest.raises(RelationshipNotFoundError):
        repository.update("rel-no-such", ExperimentHardwareRelationship(**_payload("rel-no-such", "exp-001", "hw-cir")))


def test_update_does_not_change_id(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload()))
    updated = repository.update("rel-001", ExperimentHardwareRelationship(**_payload("rel-999", "exp-001", "hw-cir", role="Updated synthetic role")))
    assert updated.id == "rel-001"
    assert repository.get_by_id("rel-999") is None
    assert repository.get_by_id("rel-001").role == "Updated synthetic role"


def test_update_duplicate_link_is_rejected(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload("rel-001", "exp-001", "hw-cir")))
    repository.create(ExperimentHardwareRelationship(**_payload("rel-002", "exp-002", "hw-msg")))
    with pytest.raises(DuplicateRelationshipReferenceError):
        repository.update("rel-002", ExperimentHardwareRelationship(**_payload("rel-002", "exp-001", "hw-cir")))
    assert repository.get_by_id("rel-002").experiment_id == "exp-002"


def test_delete_relationship_removes_only_that_record(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload("rel-001", "exp-001", "hw-cir")))
    repository.create(ExperimentHardwareRelationship(**_payload("rel-002", "exp-002", "hw-msg")))
    repository.delete("rel-001")
    assert repository.get_by_id("rel-001") is None
    assert len(repository.get_all()) == 1
    fresh = RelationshipRepository(data_dir=relationships_dir)
    assert len(fresh.get_all()) == 1


def test_delete_nonexistent_raises_not_found(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    with pytest.raises(RelationshipNotFoundError):
        repository.delete("rel-no-such")


def test_search_filters_synthetic_relationships(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload("rel-001", "exp-001", "hw-cir", relationship_type="used_in", verification_status="confirmed")))
    repository.create(ExperimentHardwareRelationship(**_payload("rel-002", "exp-001", "hw-msg", relationship_type="housed_in", role="Synthetic housing role")))
    repository.create(ExperimentHardwareRelationship(**_payload("rel-003", "exp-002", "hw-cir", relationship_type="supports", verification_status="confirmed")))
    assert len(repository.search({"experiment_id": "exp-001"})) == 2
    assert len(repository.search({"hardware_id": "hw-cir"})) == 2
    assert len(repository.search({"relationship_type": "used_in"})) == 1
    assert len(repository.search({"verification_status": "confirmed"})) == 2
    assert len(repository.search({"query": "housing"})) == 1
    assert len(repository.search({"role": "housing"})) == 1
    assert len(repository.search({})) == 3
    assert len(repository.search({"experiment_id": "exp-no-such"})) == 0


def test_empty_json_file_returns_empty_list(tmp_path):
    relationships_dir = tmp_path / "relationships"
    _write_json(relationships_dir, "experiment_hardware.json", [])
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert repository.get_all() == []


def test_malformed_json_returns_empty_list_and_records_invalid(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    file = relationships_dir / "experiment_hardware.json"
    file.write_text("{ not json", encoding="utf-8")
    before = file.read_text(encoding="utf-8")
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert repository.get_all() == []
    assert len(repository.get_invalid_records()) == 1
    assert file.read_text(encoding="utf-8") == before


def test_invalid_record_is_skipped_but_preserved(tmp_path):
    relationships_dir = tmp_path / "relationships"
    bad = _payload("rel-bad", "exp-001", "hw-cir", relationship_type="teleported")
    file = _write_json(relationships_dir, "experiment_hardware.json", [_payload(), bad])
    before = file.read_text(encoding="utf-8")
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert len(repository.get_all()) == 1
    invalid = repository.get_invalid_records()
    assert len(invalid) == 1
    assert invalid[0]["record_id"] == "rel-bad"
    assert invalid[0]["record"]["relationship_type"] == "teleported"
    assert file.read_text(encoding="utf-8") == before


def test_invalid_records_survive_update(tmp_path):
    relationships_dir = tmp_path / "relationships"
    bad = _payload("rel-bad", "exp-001", "hw-cir", relationship_type="teleported")
    file = _write_json(relationships_dir, "experiment_hardware.json", [_payload(), bad])
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.update("rel-001", ExperimentHardwareRelationship(**_payload("rel-001", "exp-001", "hw-cir", role="Updated synthetic role")))
    records = json.loads(file.read_text(encoding="utf-8"))
    ids = [record.get("id") for record in records]
    assert "rel-bad" in ids
    assert "rel-001" in ids


def test_invalid_records_survive_delete(tmp_path):
    relationships_dir = tmp_path / "relationships"
    bad = _payload("rel-bad", "exp-001", "hw-cir", relationship_type="teleported")
    file = _write_json(relationships_dir, "experiment_hardware.json", [_payload(), bad, _payload("rel-002", "exp-002", "hw-msg")])
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.delete("rel-001")
    records = json.loads(file.read_text(encoding="utf-8"))
    ids = [record.get("id") for record in records]
    assert "rel-bad" in ids
    assert "rel-001" not in ids
    assert "rel-002" in ids


def test_atomic_write_safety(tmp_path):
    relationships_dir = tmp_path / "relationships"
    relationships_dir.mkdir()
    repository = RelationshipRepository(data_dir=relationships_dir)
    repository.create(ExperimentHardwareRelationship(**_payload()))
    file = relationships_dir / "experiment_hardware.json"
    records = json.loads(file.read_text(encoding="utf-8"))
    assert len(records) == 1
    assert records[0]["id"] == "rel-001"
    assert list(relationships_dir.glob("*.tmp")) == []


def test_reload_picks_up_new_file(tmp_path):
    relationships_dir = tmp_path / "relationships"
    _write_json(relationships_dir, "experiment_hardware.json", [_payload()])
    repository = RelationshipRepository(data_dir=relationships_dir)
    assert len(repository.get_all()) == 1
    _write_json(relationships_dir, "more.json", [_payload("rel-002", "exp-002", "hw-msg")])
    repository.reload()
    assert len(repository.get_all()) == 2
