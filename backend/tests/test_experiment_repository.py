import json
import pytest
from pathlib import Path
from app.repositories.experiment_repository import DuplicateExperimentError, ExperimentNotFoundError, ExperimentRepository
from app.schemas.experiment import Experiment


def _write_json(file_path, records):
    file_path.write_text(json.dumps(records), encoding="utf-8")


def _synthetic_record(experiment_id, name, nasa_id=None, acronym=None):
    record = {"id": experiment_id, "name": name}
    if nasa_id is not None:
        record["nasa_investigation_id"] = nasa_id
    if acronym is not None:
        record["acronym"] = acronym
    return record


def test_load_empty_folder_returns_empty_list(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    assert repository.get_all() == []


def test_load_missing_folder_returns_empty_list(tmp_path):
    repository = ExperimentRepository(data_dir=tmp_path / "no-such-folder")
    assert repository.get_all() == []


def test_load_synthetic_experiments(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    records = [
        _synthetic_record("exp-001", "Synthetic FLEX test", "SYNTH-001", "SYNTH"),
        _synthetic_record("exp-002", "Synthetic ACME test", "SYNTH-002", "SYNTH2"),
    ]
    _write_json(experiments_dir / "synthetic_experiments.json", records)
    repository = ExperimentRepository(data_dir=experiments_dir)
    loaded = repository.get_all()
    assert len(loaded) == 2
    assert loaded[0].id == "exp-001"
    assert loaded[0].name == "Synthetic FLEX test"
    assert loaded[1].id == "exp-002"


def test_get_by_id_matches_id_nasa_id_and_acronym(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    records = [_synthetic_record("exp-001", "Synthetic FLEX test", "SYNTH-001", "SYNTH")]
    _write_json(experiments_dir / "synthetic_experiments.json", records)
    repository = ExperimentRepository(data_dir=experiments_dir)
    assert repository.get_by_id("exp-001").name == "Synthetic FLEX test"
    assert repository.get_by_id("SYNTH-001").id == "exp-001"
    assert repository.get_by_id("synth").id == "exp-001"
    assert repository.get_by_id("  exp-001  ").id == "exp-001"


def test_get_by_id_returns_none_for_unknown(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    records = [_synthetic_record("exp-001", "Synthetic FLEX test")]
    _write_json(experiments_dir / "synthetic_experiments.json", records)
    repository = ExperimentRepository(data_dir=experiments_dir)
    assert repository.get_by_id("no-such-id") is None


def test_invalid_record_is_skipped(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    records = [
        _synthetic_record("exp-001", "Synthetic FLEX test"),
        {"id": "exp-bad"},
    ]
    _write_json(experiments_dir / "synthetic_experiments.json", records)
    repository = ExperimentRepository(data_dir=experiments_dir)
    loaded = repository.get_all()
    assert len(loaded) == 1
    assert loaded[0].id == "exp-001"


def test_invalid_json_file_is_skipped(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    records = [_synthetic_record("exp-001", "Synthetic FLEX test")]
    _write_json(experiments_dir / "synthetic_experiments.json", records)
    (experiments_dir / "bad.json").write_text("{not json", encoding="utf-8")
    repository = ExperimentRepository(data_dir=experiments_dir)
    loaded = repository.get_all()
    assert len(loaded) == 1
    assert loaded[0].id == "exp-001"


def test_reload_picks_up_new_file(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    records = [_synthetic_record("exp-001", "Synthetic FLEX test")]
    _write_json(experiments_dir / "synthetic_experiments.json", records)
    repository = ExperimentRepository(data_dir=experiments_dir)
    assert len(repository.get_all()) == 1
    more = [_synthetic_record("exp-002", "Synthetic ACME test")]
    _write_json(experiments_dir / "more_synthetic.json", more)
    reloaded = repository.reload()
    assert len(reloaded) == 2
    assert len(repository.get_all()) == 2


def test_new_fields_preserved_after_load(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    record = _synthetic_record("exp-001", "Synthetic FLEX test")
    record["mission_applicability"] = ["ISS", "Moon"]
    record["transferability_note"] = "Synthetic note for testing only"
    record["fire_safety_relevance"] = ["prevention"]
    record["measurements"] = [
        {
            "id": "m-001",
            "experiment_id": "exp-001",
            "parameter_name": "oxygen concentration",
            "value": 20.0,
            "unit": "%",
            "measurement_kind": "derived",
        }
    ]
    _write_json(experiments_dir / "synthetic_experiments.json", [record])
    repository = ExperimentRepository(data_dir=experiments_dir)
    loaded = repository.get_all()
    assert len(loaded) == 1
    assert loaded[0].mission_applicability == ["ISS", "Moon"]
    assert loaded[0].transferability_note == "Synthetic note for testing only"
    assert loaded[0].fire_safety_relevance == ["prevention"]
    assert loaded[0].measurements[0].measurement_kind == "derived"


def test_create_experiment_saves_to_store_file(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    experiment = Experiment(id="exp-001", name="Synthetic FLEX test")
    created = repository.create(experiment)
    assert created.id == "exp-001"
    assert len(repository.get_all()) == 1
    assert (experiments_dir / "experiments.json").is_file()
    fresh = ExperimentRepository(data_dir=experiments_dir)
    assert len(fresh.get_all()) == 1
    assert fresh.get_by_id("exp-001").name == "Synthetic FLEX test"


def test_create_duplicate_id_is_rejected(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.create(Experiment(id="exp-001", name="Synthetic FLEX test"))
    with pytest.raises(DuplicateExperimentError):
        repository.create(Experiment(id="exp-001", name="Another synthetic test"))
    assert len(repository.get_all()) == 1


def test_update_experiment_preserves_other_records(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.create(Experiment(id="exp-001", name="Synthetic FLEX test", fuel_material="methanol"))
    repository.create(Experiment(id="exp-002", name="Synthetic ACME test", fuel_material="heptane"))
    updated = repository.update(
        "exp-001",
        Experiment(id="exp-001", name="Updated synthetic test", fuel_material="heptane"),
    )
    assert updated.id == "exp-001"
    assert updated.name == "Updated synthetic test"
    assert updated.fuel_material == "heptane"
    assert len(repository.get_all()) == 2
    other = repository.get_by_id("exp-002")
    assert other.name == "Synthetic ACME test"
    assert other.fuel_material == "heptane"


def test_update_nonexistent_raises_not_found(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    with pytest.raises(ExperimentNotFoundError):
        repository.update("no-such", Experiment(id="no-such", name="Synthetic test"))


def test_update_does_not_change_id(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.create(Experiment(id="exp-001", name="Synthetic FLEX test"))
    updated = repository.update(
        "exp-001",
        Experiment(id="exp-999", name="Updated synthetic test"),
    )
    assert updated.id == "exp-001"
    assert repository.get_by_id("exp-999") is None
    assert repository.get_by_id("exp-001").name == "Updated synthetic test"


def test_delete_experiment_removes_only_that_record(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.create(Experiment(id="exp-001", name="Synthetic FLEX test"))
    repository.create(Experiment(id="exp-002", name="Synthetic ACME test"))
    repository.delete("exp-001")
    assert repository.get_by_id("exp-001") is None
    assert len(repository.get_all()) == 1
    assert repository.get_by_id("exp-002").name == "Synthetic ACME test"
    fresh = ExperimentRepository(data_dir=experiments_dir)
    assert len(fresh.get_all()) == 1


def test_delete_nonexistent_raises_not_found(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    with pytest.raises(ExperimentNotFoundError):
        repository.delete("no-such")


def test_search_filters_synthetic_experiments(tmp_path):
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    repository = ExperimentRepository(data_dir=experiments_dir)
    repository.create(
        Experiment(
            id="exp-001",
            name="Synthetic FLEX test",
            research_category="droplet combustion",
            fuel_material="methanol",
            hardware_ids=["MDCA"],
            mission_applicability=["ISS"],
            fire_safety_relevance=["prevention"],
            conditions={"gravity_condition": "microgravity"},
        )
    )
    repository.create(
        Experiment(
            id="exp-002",
            name="Synthetic ACME test",
            research_category="flame spread",
            fuel_material="heptane",
            hardware_ids=["CIR"],
            mission_applicability=["Moon"],
            fire_safety_relevance=["detection"],
            conditions={"gravity_condition": "lunar"},
        )
    )
    repository.create(
        Experiment(
            id="exp-003",
            name="Synthetic FLEX-2 test",
            research_category="droplet combustion",
            fuel_material="methanol",
            hardware_ids=["MDCA"],
            mission_applicability=["Mars"],
            fire_safety_relevance=["suppression"],
            conditions={"gravity_condition": "microgravity"},
        )
    )
    assert len(repository.search({"research_category": "droplet combustion"})) == 2
    assert len(repository.search({"fuel_material": "methanol"})) == 2
    assert len(repository.search({"hardware_id": "CIR"})) == 1
    assert len(repository.search({"query": "heptane"})) == 1
    assert len(repository.search({"mission_applicability": "Moon"})) == 1
    assert len(repository.search({"fire_safety_relevance": "suppression"})) == 1
    assert len(repository.search({"gravity_condition": "microgravity"})) == 2
    assert len(repository.search({})) == 3
    assert len(repository.search({"research_category": "no-such"})) == 0
