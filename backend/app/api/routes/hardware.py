from fastapi import APIRouter, Depends, HTTPException, Query
from app.repositories.hardware_repository import DuplicateHardwareError, HardwareNotFoundError
from app.schemas.hardware import Hardware
from app.schemas.response import DeleteResponse, PaginatedHardwareList
from app.services.hardware_service import HardwareService
from app.services.relationship_service import ReferencedByRelationshipError

router = APIRouter(prefix="/v1/hardware", tags=["hardware"])


def get_service() -> HardwareService:
    return HardwareService()


@router.post("", response_model=Hardware, status_code=201)
def create_hardware(hardware: Hardware, service: HardwareService = Depends(get_service)):
    try:
        return service.create_hardware(hardware)
    except DuplicateHardwareError:
        raise HTTPException(status_code=409, detail="Hardware with this id already exists")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/search", response_model=PaginatedHardwareList)
def search_hardware(
    query: str | None = None,
    name: str | None = None,
    hardware_type: str | None = None,
    parent_hardware_id: str | None = None,
    facility_classification: str | None = None,
    supported_measurements: str | None = None,
    related_experiment_ids: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: HardwareService = Depends(get_service),
):
    filters = {}
    if query is not None:
        filters["query"] = query
    if name is not None:
        filters["name"] = name
    if hardware_type is not None:
        filters["hardware_type"] = hardware_type
    if parent_hardware_id is not None:
        filters["parent_hardware_id"] = parent_hardware_id
    if facility_classification is not None:
        filters["facility_classification"] = facility_classification
    if supported_measurements is not None:
        filters["supported_measurements"] = supported_measurements
    if related_experiment_ids is not None:
        filters["related_experiment_ids"] = related_experiment_ids
    try:
        return service.search_hardware(filters, page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=PaginatedHardwareList)
def list_hardware(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: HardwareService = Depends(get_service),
):
    try:
        return service.list_hardware(page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{hardware_id}", response_model=Hardware)
def get_hardware(hardware_id: str, service: HardwareService = Depends(get_service)):
    try:
        return service.get_hardware(hardware_id)
    except HardwareNotFoundError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{hardware_id}", response_model=Hardware)
def update_hardware(hardware_id: str, hardware: Hardware, service: HardwareService = Depends(get_service)):
    try:
        return service.update_hardware(hardware_id, hardware)
    except HardwareNotFoundError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{hardware_id}", response_model=DeleteResponse)
def delete_hardware(hardware_id: str, service: HardwareService = Depends(get_service)):
    try:
        service.delete_hardware(hardware_id)
        return DeleteResponse(message="Hardware deleted", deleted_id=hardware_id)
    except ReferencedByRelationshipError:
        raise HTTPException(status_code=409, detail="Cannot delete hardware because relationships exist")
    except HardwareNotFoundError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
