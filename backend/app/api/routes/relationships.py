from fastapi import APIRouter, Depends, HTTPException, Query
from app.repositories.relationship_repository import DuplicateRelationshipError, DuplicateRelationshipReferenceError, RelationshipNotFoundError
from app.schemas.relationship import ExperimentHardwareRelationship
from app.schemas.response import DeleteResponse, PaginatedRelationshipList
from app.services.relationship_service import InvalidExperimentReferenceError, InvalidHardwareReferenceError, RelationshipService

router = APIRouter(prefix="/v1/relationships", tags=["relationships"])


def get_service() -> RelationshipService:
    return RelationshipService()


@router.post("", response_model=ExperimentHardwareRelationship, status_code=201)
def create_relationship(relationship: ExperimentHardwareRelationship, service: RelationshipService = Depends(get_service)):
    try:
        return service.create_relationship(relationship)
    except DuplicateRelationshipError:
        raise HTTPException(status_code=409, detail="Relationship with this id already exists")
    except DuplicateRelationshipReferenceError:
        raise HTTPException(status_code=409, detail="Relationship for this experiment, hardware and type already exists")
    except InvalidExperimentReferenceError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except InvalidHardwareReferenceError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/search", response_model=PaginatedRelationshipList)
def search_relationships(
    query: str | None = None,
    experiment_id: str | None = None,
    hardware_id: str | None = None,
    relationship_type: str | None = None,
    verification_status: str | None = None,
    role: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: RelationshipService = Depends(get_service),
):
    filters = {}
    if query is not None:
        filters["query"] = query
    if experiment_id is not None:
        filters["experiment_id"] = experiment_id
    if hardware_id is not None:
        filters["hardware_id"] = hardware_id
    if relationship_type is not None:
        filters["relationship_type"] = relationship_type
    if verification_status is not None:
        filters["verification_status"] = verification_status
    if role is not None:
        filters["role"] = role
    try:
        return service.search_relationships(filters, page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/by-experiment/{experiment_id}", response_model=PaginatedRelationshipList)
def get_by_experiment(
    experiment_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: RelationshipService = Depends(get_service),
):
    try:
        return service.get_by_experiment(experiment_id, page=page, page_size=page_size)
    except InvalidExperimentReferenceError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/by-hardware/{hardware_id}", response_model=PaginatedRelationshipList)
def get_by_hardware(
    hardware_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: RelationshipService = Depends(get_service),
):
    try:
        return service.get_by_hardware(hardware_id, page=page, page_size=page_size)
    except InvalidHardwareReferenceError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=PaginatedRelationshipList)
def list_relationships(
    experiment_id: str | None = None,
    hardware_id: str | None = None,
    relationship_type: str | None = None,
    verification_status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: RelationshipService = Depends(get_service),
):
    filters = {}
    if experiment_id is not None:
        filters["experiment_id"] = experiment_id
    if hardware_id is not None:
        filters["hardware_id"] = hardware_id
    if relationship_type is not None:
        filters["relationship_type"] = relationship_type
    if verification_status is not None:
        filters["verification_status"] = verification_status
    try:
        return service.search_relationships(filters, page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{relationship_id}", response_model=ExperimentHardwareRelationship)
def get_relationship(relationship_id: str, service: RelationshipService = Depends(get_service)):
    try:
        return service.get_relationship(relationship_id)
    except RelationshipNotFoundError:
        raise HTTPException(status_code=404, detail="Relationship not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{relationship_id}", response_model=ExperimentHardwareRelationship)
def update_relationship(relationship_id: str, relationship: ExperimentHardwareRelationship, service: RelationshipService = Depends(get_service)):
    try:
        return service.update_relationship(relationship_id, relationship)
    except RelationshipNotFoundError:
        raise HTTPException(status_code=404, detail="Relationship not found")
    except DuplicateRelationshipReferenceError:
        raise HTTPException(status_code=409, detail="Relationship for this experiment, hardware and type already exists")
    except InvalidExperimentReferenceError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except InvalidHardwareReferenceError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{relationship_id}", response_model=DeleteResponse)
def delete_relationship(relationship_id: str, service: RelationshipService = Depends(get_service)):
    try:
        service.delete_relationship(relationship_id)
        return DeleteResponse(message="Relationship deleted", deleted_id=relationship_id)
    except RelationshipNotFoundError:
        raise HTTPException(status_code=404, detail="Relationship not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
