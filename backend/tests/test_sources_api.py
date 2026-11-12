import pytest
from fastapi.testclient import TestClient

from app.api.routes.sources import get_service
from app.repositories.source_repository import SourceRepository
from app.services.source_service import SourceService
from main import app


def make_payload(source_id="src-001", **overrides):
    data = {
        "id": source_id,
        "source_type": "nasa_report",
        "title": "FLEX Experiment Overview",
        "nasa_report_id": "PSI-69",
        "doi": "10.60555/mbq8-0451",
        "url": "https://example.nasa.gov/flex",
        "publisher": "NASA Glenn Research Center",
    }
    data.update(overrides)
    return data


@pytest.fixture
def client(tmp_path):
    repository = SourceRepository(data_dir=tmp_path)
    service = SourceService(repository=repository)
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_source_returns_201(client):
    response = client.post("/api/v1/sources", json=make_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "src-001"
    assert body["title"] == "FLEX Experiment Overview"
    assert body["verification_status"] == "unverified"


def test_create_duplicate_returns_409(client):
    client.post("/api/v1/sources", json=make_payload())
    response = client.post("/api/v1/sources", json=make_payload())
    assert response.status_code == 409


def test_create_missing_title_returns_422(client):
    response = client.post("/api/v1/sources", json={"id": "src-002"})
    assert response.status_code == 422


def test_create_invalid_doi_returns_422(client):
    response = client.post("/api/v1/sources", json=make_payload(doi="not-a-doi"))
    assert response.status_code == 422


def test_create_invalid_url_returns_422(client):
    response = client.post("/api/v1/sources", json=make_payload(url="ftp://example.nasa.gov/flex"))
    assert response.status_code == 422


def test_list_sources_empty(client):
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["total_pages"] == 0
    assert body["items"] == []


def test_list_sources_pagination(client):
    client.post("/api/v1/sources", json=make_payload())
    client.post("/api/v1/sources", json=make_payload(source_id="src-002", title="Second"))
    client.post("/api/v1/sources", json=make_payload(source_id="src-003", title="Third"))
    first = client.get("/api/v1/sources?page=1&page_size=2")
    assert first.status_code == 200
    assert first.json()["total"] == 3
    assert first.json()["total_pages"] == 2
    assert len(first.json()["items"]) == 2
    second = client.get("/api/v1/sources?page=2&page_size=2")
    assert len(second.json()["items"]) == 1


def test_list_invalid_page_returns_422(client):
    response = client.get("/api/v1/sources?page=0")
    assert response.status_code == 422


def test_get_source_by_id(client):
    client.post("/api/v1/sources", json=make_payload())
    response = client.get("/api/v1/sources/src-001")
    assert response.status_code == 200
    assert response.json()["title"] == "FLEX Experiment Overview"


def test_get_source_missing_returns_404(client):
    response = client.get("/api/v1/sources/src-999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Source not found"


def test_search_sources_by_query(client):
    client.post("/api/v1/sources", json=make_payload())
    client.post("/api/v1/sources", json=make_payload(source_id="src-002", title="Microgravity Combustion Review", source_type="paper"))
    response = client.get("/api/v1/sources/search?query=flex")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_search_sources_by_verification_status(client):
    client.post("/api/v1/sources", json=make_payload())
    client.post("/api/v1/sources", json=make_payload(source_id="src-002", title="Second", verification_status="confirmed"))
    response = client.get("/api/v1/sources/search?verification_status=confirmed")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == "src-002"


def test_search_sources_by_source_type(client):
    client.post("/api/v1/sources", json=make_payload())
    client.post("/api/v1/sources", json=make_payload(source_id="src-002", title="Second", source_type="paper"))
    response = client.get("/api/v1/sources/search?source_type=paper")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_source(client):
    client.post("/api/v1/sources", json=make_payload())
    response = client.put("/api/v1/sources/src-001", json=make_payload(title="FLEX Updated"))
    assert response.status_code == 200
    assert response.json()["title"] == "FLEX Updated"
    assert response.json()["id"] == "src-001"


def test_update_missing_returns_404(client):
    response = client.put("/api/v1/sources/src-999", json=make_payload(source_id="src-999"))
    assert response.status_code == 404


def test_delete_source(client):
    client.post("/api/v1/sources", json=make_payload())
    response = client.delete("/api/v1/sources/src-001")
    assert response.status_code == 200
    assert response.json()["message"] == "Source deleted"
    assert response.json()["deleted_id"] == "src-001"
    assert client.get("/api/v1/sources/src-001").status_code == 404


def test_delete_missing_returns_404(client):
    response = client.delete("/api/v1/sources/src-999")
    assert response.status_code == 404


def test_set_verification_confirmed(client):
    client.post("/api/v1/sources", json=make_payload())
    response = client.post("/api/v1/sources/src-001/verification", json={"verification_status": "confirmed"})
    assert response.status_code == 200
    assert response.json()["verification_status"] == "confirmed"
    assert response.json()["title"] == "FLEX Experiment Overview"


def test_set_verification_failed(client):
    client.post("/api/v1/sources", json=make_payload())
    response = client.post("/api/v1/sources/src-001/verification", json={"verification_status": "verification_failed"})
    assert response.status_code == 200
    assert response.json()["verification_status"] == "verification_failed"


def test_set_verification_invalid_value_returns_422(client):
    client.post("/api/v1/sources", json=make_payload())
    response = client.post("/api/v1/sources/src-001/verification", json={"verification_status": "verified"})
    assert response.status_code == 422


def test_set_verification_missing_returns_404(client):
    response = client.post("/api/v1/sources/src-999/verification", json={"verification_status": "confirmed"})
    assert response.status_code == 404
