from fastapi import APIRouter, Depends, HTTPException, Query
from app.repositories.experiment_repository import DuplicateExperimentError, ExperimentNotFoundError
from app.schemas.experiment import Experiment
from app.schemas.response import DeleteResponse, PaginatedExperimentList
from app.services.experiment_service import ExperimentService
from app.services.relationship_service import ReferencedByRelationshipError

router = APIRouter(prefix="/v1/experiments", tags=["experiments"])


def get_service() -> ExperimentService:
    return ExperimentService()


@router.post("", response_model=Experiment, status_code=201)
def create_experiment(experiment: Experiment, service: ExperimentService = Depends(get_service)):
    try:
        return service.create_experiment(experiment)
    except DuplicateExperimentError:
        raise HTTPException(status_code=409, detail="Experiment with this id already exists")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/search", response_model=PaginatedExperimentList)
def search_experiments(
    query: str | None = None,
    research_category: str | None = None,
    fuel_material: str | None = None,
    hardware_id: str | None = None,
    gravity_condition: str | None = None,
    mission_applicability: str | None = None,
    fire_safety_relevance: str | None = None,
    data_completeness: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ExperimentService = Depends(get_service),
):
    filters = {}
    if query is not None:
        filters["query"] = query
    if research_category is not None:
        filters["research_category"] = research_category
    if fuel_material is not None:
        filters["fuel_material"] = fuel_material
    if hardware_id is not None:
        filters["hardware_id"] = hardware_id
    if gravity_condition is not None:
        filters["gravity_condition"] = gravity_condition
    if mission_applicability is not None:
        filters["mission_applicability"] = mission_applicability
    if fire_safety_relevance is not None:
        filters["fire_safety_relevance"] = fire_safety_relevance
    if data_completeness is not None:
        filters["data_completeness"] = data_completeness
    try:
        return service.search_experiments(filters, page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=PaginatedExperimentList)
def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ExperimentService = Depends(get_service),
):
    try:
        return service.list_experiments(page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{experiment_id}", response_model=Experiment)
def get_experiment(experiment_id: str, service: ExperimentService = Depends(get_service)):
    try:
        return service.get_experiment(experiment_id)
    except ExperimentNotFoundError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{experiment_id}", response_model=Experiment)
def update_experiment(experiment_id: str, experiment: Experiment, service: ExperimentService = Depends(get_service)):
    try:
        return service.update_experiment(experiment_id, experiment)
    except ExperimentNotFoundError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{experiment_id}", response_model=DeleteResponse)
def delete_experiment(experiment_id: str, service: ExperimentService = Depends(get_service)):
    try:
        service.delete_experiment(experiment_id)
        return DeleteResponse(message="Experiment deleted", deleted_id=experiment_id)
    except ReferencedByRelationshipError:
        raise HTTPException(status_code=409, detail="Cannot delete experiment because relationships exist")
    except ExperimentNotFoundError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
