import pytest
from fastapi.testclient import TestClient
from main import app
from app.api.routes.hardware import get_service
from app.repositories.hardware_repository import HardwareRepository
from app.services.hardware_service import HardwareService


@pytest.fixture
def client(tmp_path):
    hardware_dir = tmp_path / "hardware"
    hardware_dir.mkdir()
    repository = HardwareRepository(data_dir=hardware_dir)
    service = HardwareService(repository=repository)
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


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


def test_create_valid_hardware(client):
    payload = _payload()
    payload["component_ids"] = ["hw-mdca"]
    payload["image_ids"] = ["img-001"]
    payload["diagram_ids"] = ["diag-001"]
    payload["source_ids"] = ["src-001"]
    payload["limitations"] = "Synthetic limitation for testing only"
    response = client.post("/api/v1/hardware", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == "hw-cir"
    assert response.json()["name"] == "Synthetic Combustion Integrated Rack"
    assert response.json()["hardware_type"] == "facility"
    assert response.json()["image_ids"] == ["img-001"]
    assert response.json()["diagram_ids"] == ["diag-001"]
    assert response.json()["source_ids"] == ["src-001"]
    assert response.json()["limitations"] == "Synthetic limitation for testing only"


def test_get_all_hardware(client):
    client.post("/api/v1/hardware", json=_payload("hw-cir", "Synthetic Combustion Integrated Rack"))
    client.post("/api/v1/hardware", json=_payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus"))
    response = client.get("/api/v1/hardware")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2


def test_get_hardware_by_id(client):
    client.post("/api/v1/hardware", json=_payload())
    response = client.get("/api/v1/hardware/hw-cir")
    assert response.status_code == 200
    assert response.json()["id"] == "hw-cir"
    response = client.get("/api/v1/hardware/CIR")
    assert response.status_code == 200
    assert response.json()["id"] == "hw-cir"


def test_update_hardware(client):
    client.post("/api/v1/hardware", json=_payload("hw-cir", "Synthetic Combustion Integrated Rack"))
    client.post("/api/v1/hardware", json=_payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus"))
    response = client.put("/api/v1/hardware/hw-cir", json=_payload("hw-cir", "Updated synthetic rack"))
    assert response.status_code == 200
    assert response.json()["name"] == "Updated synthetic rack"
    other = client.get("/api/v1/hardware/hw-mdca")
    assert other.json()["name"] == "Synthetic Droplet Combustion Apparatus"


def test_delete_hardware(client):
    client.post("/api/v1/hardware", json=_payload("hw-cir", "Synthetic Combustion Integrated Rack"))
    client.post("/api/v1/hardware", json=_payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus"))
    response = client.delete("/api/v1/hardware/hw-cir")
    assert response.status_code == 200
    assert response.json()["deleted_id"] == "hw-cir"
    assert client.get("/api/v1/hardware/hw-cir").status_code == 404
    listed = client.get("/api/v1/hardware")
    assert listed.json()["total"] == 1


def test_search_hardware(client):
    client.post("/api/v1/hardware", json=_payload("hw-cir", "Synthetic Combustion Integrated Rack"))
    client.post("/api/v1/hardware", json=_payload("hw-msg", "Synthetic Microgravity Science Glovebox", acronym="MSG", facility_classification="glovebox"))
    response = client.get("/api/v1/hardware/search", params={"query": "glovebox"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == "hw-msg"
    response = client.get("/api/v1/hardware/search", params={"query": "integrated"})
    assert response.json()["total"] == 1


def test_filter_by_hardware_type(client):
    client.post("/api/v1/hardware", json=_payload("hw-cir", "Synthetic Combustion Integrated Rack", hardware_type="facility"))
    client.post("/api/v1/hardware", json=_payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus"))
    client.post("/api/v1/hardware", json=_payload("hw-msg", "Synthetic Microgravity Science Glovebox", acronym="MSG", hardware_type="facility"))
    response = client.get("/api/v1/hardware/search", params={"hardware_type": "facility"})
    assert response.json()["total"] == 2
    response = client.get("/api/v1/hardware/search", params={"hardware_type": "apparatus"})
    assert response.json()["total"] == 1


def test_filter_by_other_supported_fields(client):
    client.post("/api/v1/hardware", json=_payload("hw-cir", "Synthetic Combustion Integrated Rack"))
    client.post(
        "/api/v1/hardware",
        json=_payload(
            "hw-mdca",
            "Synthetic Droplet Combustion Apparatus",
            acronym="MDCA",
            hardware_type="apparatus",
            parent_hardware_id="hw-cir",
            facility_classification="droplet apparatus",
            supported_measurements=["droplet diameter"],
            related_experiment_ids=["exp-001"],
        ),
    )
    client.post("/api/v1/hardware", json=_payload("hw-msg", "Synthetic Microgravity Science Glovebox", acronym="MSG", facility_classification="glovebox"))
    assert client.get("/api/v1/hardware/search", params={"parent_hardware_id": "hw-cir"}).json()["total"] == 1
    assert client.get("/api/v1/hardware/search", params={"facility_classification": "glovebox"}).json()["total"] == 1
    assert client.get("/api/v1/hardware/search", params={"supported_measurements": "droplet diameter"}).json()["total"] == 1
    assert client.get("/api/v1/hardware/search", params={"related_experiment_ids": "exp-001"}).json()["total"] == 1
    assert client.get("/api/v1/hardware/search", params={"name": "Glovebox"}).json()["total"] == 1


def test_pagination_works(client):
    client.post("/api/v1/hardware", json=_payload("hw-cir", "Synthetic Combustion Integrated Rack"))
    client.post("/api/v1/hardware", json=_payload("hw-mdca", "Synthetic Droplet Combustion Apparatus", acronym="MDCA", hardware_type="apparatus"))
    client.post("/api/v1/hardware", json=_payload("hw-msg", "Synthetic Microgravity Science Glovebox", acronym="MSG"))
    first = client.get("/api/v1/hardware", params={"page": 1, "page_size": 2})
    assert first.status_code == 200
    assert first.json()["total"] == 3
    assert first.json()["total_pages"] == 2
    assert len(first.json()["items"]) == 2
    second = client.get("/api/v1/hardware", params={"page": 2, "page_size": 2})
    assert len(second.json()["items"]) == 1


def test_empty_dataset_returns_empty_response(client):
    response = client.get("/api/v1/hardware")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["total_pages"] == 0
    assert response.json()["items"] == []
    searched = client.get("/api/v1/hardware/search", params={"query": "cir"})
    assert searched.json()["total"] == 0
    assert searched.json()["items"] == []


def test_duplicate_hardware_id_is_rejected(client):
    client.post("/api/v1/hardware", json=_payload())
    response = client.post("/api/v1/hardware", json=_payload())
    assert response.status_code == 409


def test_invalid_hardware_payload_is_rejected(client):
    response = client.post("/api/v1/hardware", json={"id": "hw-bad"})
    assert response.status_code == 422
    response = client.post("/api/v1/hardware", json=_payload("hw-bad", "Synthetic bad hardware", hardware_type="spaceship"))
    assert response.status_code == 422


def test_nonexistent_hardware_returns_404(client):
    assert client.get("/api/v1/hardware/hw-no-such").status_code == 404
    assert client.put("/api/v1/hardware/hw-no-such", json=_payload("hw-no-such", "Synthetic test")).status_code == 404
    assert client.delete("/api/v1/hardware/hw-no-such").status_code == 404


def test_invalid_pagination_values_are_rejected(client):
    assert client.get("/api/v1/hardware", params={"page": 0}).status_code == 422
    assert client.get("/api/v1/hardware", params={"page_size": 0}).status_code == 422
    assert client.get("/api/v1/hardware", params={"page_size": 101}).status_code == 422


def test_hardware_classification_validation(client):
    for hardware_type in ["facility", "apparatus", "component", "instrument"]:
        payload = _payload(f"hw-{hardware_type}", f"Synthetic {hardware_type}", hardware_type=hardware_type)
        response = client.post("/api/v1/hardware", json=payload)
        assert response.status_code == 201
        assert response.json()["hardware_type"] == hardware_type
    response = client.post("/api/v1/hardware", json=_payload("hw-bad", "Synthetic bad hardware", hardware_type="rack"))
    assert response.status_code == 422


def test_existing_module02_and_module03_functionality_remains_intact(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    experiments = client.get("/api/v1/experiments")
    assert experiments.status_code == 200
    assert experiments.json()["total"] == 0
    assert experiments.json()["items"] == []
