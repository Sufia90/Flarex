import json
import pytest
from pathlib import Path
from app.repositories.hardware_repository import DuplicateHardwareError, HardwareNotFoundError, HardwareRepository
from app.schemas.hardware import Hardware


def _payload(hardware_id="hw-cir", name="Synthetic Combustion Integrated Rack", **overrides):
    payload = {
        "id": hardware_id,
        "name": name,
        "acronym": "CIR",
        "hardware_type": "facility",
        "description": "Synthetic rack for testing only",
        "purpose": "Synthetic purpose for testing only",
        "facility_classification": "combustion rack",
        "supported_measurements": ["temperature", "pressure"],
        "related_experiment_ids": [],
    }
    payload.update(overrides)
    return payload


def _write_json(directory: Path, filename: str, records) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    file = directory / filename
    file.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return file


def test_empty_folder_returns_empty_list(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    assert repository.get_all() == []
    assert repository.get_invalid_records() == []


def test_missing_folder_returns_empty_list(tmp_path):
    repository = HardwareRepository(data_dir=tmp_path / "hardware")
    assert repository.get_all() == []


def test_load_hardware_records(tmp_path):
    hardware_dir = tmp_path / "hardware"
    _write_json(hardware_dir, "hardware.json", [_payload(), _payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus", parent_hardware_id="hw-cir")])
    repository = HardwareRepository(data_dir=hardware_dir)
    assert len(repository.get_all()) == 2
    assert repository.get_all()[0].name == "Synthetic Combustion Integrated Rack"


def test_get_by_id(tmp_path):
    hardware_dir = tmp_path / "hardware"
    _write_json(hardware_dir, "hardware.json", [_payload()])
    repository = HardwareRepository(data_dir=hardware_dir)
    assert repository.get_by_id("hw-cir").name == "Synthetic Combustion Integrated Rack"
    assert repository.get_by_id("CIR").id == "hw-cir"
    assert repository.get_by_id("hw-no-such") is None


def test_create_hardware_saves_to_store_file(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    created = repository.create(Hardware(**_payload()))
    assert created.id == "hw-cir"
    assert len(repository.get_all()) == 1
    assert (hardware_dir / "hardware.json").is_file()
    fresh = HardwareRepository(data_dir=hardware_dir)
    assert len(fresh.get_all()) == 1
    assert fresh.get_by_id("hw-cir").name == "Synthetic Combustion Integrated Rack"


def test_create_duplicate_id_is_rejected(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    repository.create(Hardware(**_payload()))
    with pytest.raises(DuplicateHardwareError):
        repository.create(Hardware(**_payload()))
    assert len(repository.get_all()) == 1


def test_update_hardware_preserves_other_records(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    repository.create(Hardware(**_payload("hw-cir", "Synthetic Combustion Integrated Rack")))
    repository.create(Hardware(**_payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus")))
    updated = repository.update("hw-cir", Hardware(**_payload("hw-cir", "Updated synthetic rack")))
    assert updated.name == "Updated synthetic rack"
    assert len(repository.get_all()) == 2
    assert repository.get_by_id("hw-mdca").name == "Synthetic Droplet Combustion Apparatus"


def test_update_nonexistent_raises_not_found(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    with pytest.raises(HardwareNotFoundError):
        repository.update("hw-no-such", Hardware(**_payload("hw-no-such", "Synthetic test")))


def test_update_does_not_change_id(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    repository.create(Hardware(**_payload()))
    updated = repository.update("hw-cir", Hardware(**_payload("hw-other", "Updated synthetic rack")))
    assert updated.id == "hw-cir"
    assert repository.get_by_id("hw-other") is None
    assert repository.get_by_id("hw-cir").name == "Updated synthetic rack"


def test_delete_hardware_removes_only_that_record(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    repository.create(Hardware(**_payload("hw-cir", "Synthetic Combustion Integrated Rack")))
    repository.create(Hardware(**_payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus")))
    repository.delete("hw-cir")
    assert repository.get_by_id("hw-cir") is None
    assert len(repository.get_all()) == 1
    fresh = HardwareRepository(data_dir=hardware_dir)
    assert len(fresh.get_all()) == 1


def test_delete_nonexistent_raises_not_found(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    with pytest.raises(HardwareNotFoundError):
        repository.delete("hw-no-such")


def test_search_filters_synthetic_hardware(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    repository.create(Hardware(**_payload("hw-cir", "Synthetic Combustion Integrated Rack", hardware_type="facility", facility_classification="combustion rack")))
    repository.create(Hardware(**_payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus", parent_hardware_id="hw-cir", supported_measurements=["droplet diameter"], related_experiment_ids=["exp-001"])))
    repository.create(Hardware(**_payload("hw-msg", "Synthetic Microgravity Science Glovebox", acronym="MSG", hardware_type="facility", facility_classification="glovebox", supported_measurements=["temperature"])))
    assert len(repository.search({"hardware_type": "facility"})) == 2
    assert len(repository.search({"hardware_type": "apparatus"})) == 1
    assert len(repository.search({"parent_hardware_id": "hw-cir"})) == 1
    assert len(repository.search({"facility_classification": "glovebox"})) == 1
    assert len(repository.search({"supported_measurements": "temperature"})) == 2
    assert len(repository.search({"related_experiment_ids": "exp-001"})) == 1
    assert len(repository.search({"query": "glovebox"})) == 1
    assert len(repository.search({})) == 3
    assert len(repository.search({"hardware_type": "no-such"})) == 0


def test_empty_json_file_returns_empty_list(tmp_path):
    hardware_dir = tmp_path / "hardware"
    _write_json(hardware_dir, "hardware.json", [])
    repository = HardwareRepository(data_dir=hardware_dir)
    assert repository.get_all() == []


def test_malformed_json_returns_empty_list_and_records_invalid(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    file = hardware_dir / "hardware.json"
    file.write_text("{ not json", encoding="utf-8")
    before = file.read_text(encoding="utf-8")
    repository = HardwareRepository(data_dir=hardware_dir)
    assert repository.get_all() == []
    assert len(repository.get_invalid_records()) == 1
    assert file.read_text(encoding="utf-8") == before


def test_invalid_record_is_skipped_but_preserved(tmp_path):
    hardware_dir = tmp_path / "hardware"
    bad = _payload("hw-bad", "Synthetic bad hardware", hardware_type="spaceship")
    file = _write_json(hardware_dir, "hardware.json", [_payload(), bad])
    before = file.read_text(encoding="utf-8")
    repository = HardwareRepository(data_dir=hardware_dir)
    assert len(repository.get_all()) == 1
    invalid = repository.get_invalid_records()
    assert len(invalid) == 1
    assert invalid[0]["record_id"] == "hw-bad"
    assert invalid[0]["record"]["hardware_type"] == "spaceship"
    assert file.read_text(encoding="utf-8") == before


def test_update_preserves_invalid_records_in_file(tmp_path):
    hardware_dir = tmp_path / "hardware"
    bad = _payload("hw-bad", "Synthetic bad hardware", hardware_type="spaceship")
    file = _write_json(hardware_dir, "hardware.json", [_payload(), bad])
    repository = HardwareRepository(data_dir=hardware_dir)
    repository.update("hw-cir", Hardware(**_payload("hw-cir", "Updated synthetic rack")))
    records = json.loads(file.read_text(encoding="utf-8"))
    ids = [record.get("id") for record in records]
    assert "hw-bad" in ids
    assert "hw-cir" in ids
    updated = [record for record in records if record.get("id") == "hw-cir"][0]
    assert updated["name"] == "Updated synthetic rack"


def test_reload_picks_up_new_file(tmp_path):
    hardware_dir = tmp_path / "hardware"
    _write_json(hardware_dir, "hardware.json", [_payload()])
    repository = HardwareRepository(data_dir=hardware_dir)
    assert len(repository.get_all()) == 1
    _write_json(hardware_dir, "more.json", [_payload("hw-msg", "Synthetic Microgravity Science Glovebox", acronym="MSG")])
    repository.reload()
    assert len(repository.get_all()) == 2
