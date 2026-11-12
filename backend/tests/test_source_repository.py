import json

import pytest

from app.repositories.source_repository import DuplicateSourceError, SourceNotFoundError, SourceRepository
from app.schemas.common import VerificationStatus
from app.schemas.relationship import Source


def make_source(source_id="src-001", **overrides):
    data = {
        "id": source_id,
        "source_type": "nasa_report",
        "title": "FLEX Experiment Overview",
        "nasa_report_id": "PSI-69",
        "doi": "10.60555/mbq8-0451",
        "url": "https://example.nasa.gov/flex",
        "publisher": "NASA Glenn Research Center",
        "description": "FLEX investigation overview.",
    }
    data.update(overrides)
    return Source(**data)


@pytest.fixture
def repo(tmp_path):
    return SourceRepository(data_dir=tmp_path)


def test_empty_data_dir(repo):
    assert repo.get_all() == []
    assert repo.get_invalid_records() == []


def test_create_and_get_source(repo):
    created = repo.create(make_source())
    assert created.id == "src-001"
    assert created.title == "FLEX Experiment Overview"
    assert created.verification_status == VerificationStatus.UNVERIFIED
    found = repo.get_by_id("src-001")
    assert found is not None
    assert found.title == "FLEX Experiment Overview"
    assert found.doi == "10.60555/mbq8-0451"


def test_create_writes_sources_json(repo, tmp_path):
    repo.create(make_source())
    saved = json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["id"] == "src-001"


def test_create_duplicate_id_raises(repo):
    repo.create(make_source())
    with pytest.raises(DuplicateSourceError):
        repo.create(make_source(title="Another title"))


def test_create_duplicate_id_case_insensitive(repo):
    repo.create(make_source())
    with pytest.raises(DuplicateSourceError):
        repo.create(make_source(source_id="SRC-001"))


def test_get_by_id_case_insensitive(repo):
    repo.create(make_source())
    assert repo.get_by_id("SRC-001") is not None
    assert repo.get_by_id("  src-001  ").title == "FLEX Experiment Overview"


def test_get_by_id_missing_returns_none(repo):
    assert repo.get_by_id("src-999") is None


def test_update_source(repo):
    repo.create(make_source())
    updated = repo.update("src-001", make_source(title="FLEX Updated"))
    assert updated.id == "src-001"
    assert updated.title == "FLEX Updated"
    assert repo.get_by_id("src-001").title == "FLEX Updated"


def test_update_forces_url_id(repo):
    repo.create(make_source())
    updated = repo.update("src-001", make_source(source_id="src-other", title="Changed"))
    assert updated.id == "src-001"
    assert updated.title == "Changed"
    assert repo.get_by_id("src-other") is None


def test_update_missing_raises(repo):
    with pytest.raises(SourceNotFoundError):
        repo.update("src-999", make_source(source_id="src-999"))


def test_delete_source(repo):
    repo.create(make_source())
    deleted = repo.delete("src-001")
    assert deleted.id == "src-001"
    assert repo.get_by_id("src-001") is None
    repo.reload()
    assert repo.get_all() == []


def test_delete_missing_raises(repo):
    with pytest.raises(SourceNotFoundError):
        repo.delete("src-999")


def _seed_two_sources(repo):
    repo.create(make_source())
    repo.create(make_source(source_id="src-002", source_type="paper", title="Microgravity Combustion Review", nasa_report_id=None, doi="10.1234/review", publisher="Journal of Combustion", description="Review of microgravity combustion research.", verification_status=VerificationStatus.CONFIRMED))


def test_search_by_query(repo):
    _seed_two_sources(repo)
    assert len(repo.search({"query": "flex"})) == 1
    assert len(repo.search({"query": "10."})) == 2
    assert len(repo.search({"query": "combustion"})) == 1
    assert len(repo.search({"query": "no-such-text"})) == 0


def test_search_by_source_type(repo):
    _seed_two_sources(repo)
    assert len(repo.search({"source_type": "paper"})) == 1
    assert len(repo.search({"source_type": "nasa_report"})) == 1


def test_search_by_verification_status(repo):
    _seed_two_sources(repo)
    assert len(repo.search({"verification_status": "confirmed"})) == 1
    assert len(repo.search({"verification_status": "unverified"})) == 1


def test_search_by_nasa_report_id(repo):
    _seed_two_sources(repo)
    assert len(repo.search({"nasa_report_id": "psi-69"})) == 1
    assert len(repo.search({"nasa_report_id": "PSI-70"})) == 0


def test_search_by_publisher(repo):
    _seed_two_sources(repo)
    assert len(repo.search({"publisher": "glenn"})) == 1
    assert len(repo.search({"publisher": "journal"})) == 1


def test_verification_failed_roundtrip(repo):
    repo.create(make_source(verification_status=VerificationStatus.VERIFICATION_FAILED))
    found = repo.get_by_id("src-001")
    assert found.verification_status == VerificationStatus.VERIFICATION_FAILED
    repo.reload()
    found = repo.get_by_id("src-001")
    assert found.verification_status == VerificationStatus.VERIFICATION_FAILED


def test_invalid_record_preserved_on_update(repo, tmp_path):
    valid = make_source()
    raw = [valid.model_dump(mode="json"), {"id": "src-bad", "source_type": "nasa_report"}]
    (tmp_path / "sources.json").write_text(json.dumps(raw), encoding="utf-8")
    repo.reload()
    assert len(repo.get_all()) == 1
    assert len(repo.get_invalid_records()) == 1
    repo.update("src-001", make_source(title="FLEX Updated"))
    saved = json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))
    assert len(saved) == 2
    assert saved[0]["title"] == "FLEX Updated"
    assert saved[1]["id"] == "src-bad"


def test_malformed_json_file_loads_empty(repo, tmp_path):
    (tmp_path / "sources.json").write_text("{not json", encoding="utf-8")
    repo.reload()
    assert repo.get_all() == []
    assert len(repo.get_invalid_records()) == 1


def test_non_list_file_loads_empty(repo, tmp_path):
    (tmp_path / "sources.json").write_text(json.dumps({"id": "src-001"}), encoding="utf-8")
    repo.reload()
    assert repo.get_all() == []
    assert len(repo.get_invalid_records()) == 1


def test_duplicate_id_across_files_keeps_first(repo, tmp_path):
    first = make_source(title="First")
    second = make_source(title="Second")
    (tmp_path / "a.json").write_text(json.dumps([first.model_dump(mode="json")]), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps([second.model_dump(mode="json")]), encoding="utf-8")
    repo.reload()
    assert len(repo.get_all()) == 1
    assert repo.get_all()[0].title == "First"
    assert len(repo.get_invalid_records()) == 1


def test_reload_picks_up_new_file(repo, tmp_path):
    repo.create(make_source())
    (tmp_path / "extra.json").write_text(json.dumps([make_source(source_id="src-003", title="Extra").model_dump(mode="json")]), encoding="utf-8")
    repo.reload()
    assert len(repo.get_all()) == 2
    assert repo.get_by_id("src-003") is not None
