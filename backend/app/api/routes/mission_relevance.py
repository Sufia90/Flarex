from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.experiment_repository import ExperimentNotFoundError
from app.repositories.hardware_repository import HardwareNotFoundError
from app.schemas.mission_relevance import MissionRelevanceAssessment
from app.services.mission_relevance_service import MissionRelevanceService

router = APIRouter(prefix="/v1/mission-relevance", tags=["mission-relevance"])


def get_service() -> MissionRelevanceService:
    return MissionRelevanceService()


@router.get("/experiments/{experiment_id}", response_model=MissionRelevanceAssessment)
def get_experiment_mission_relevance(experiment_id: str, mission: str = Query(...), service: MissionRelevanceService = Depends(get_service)):
    try:
        return service.assess_experiment(experiment_id, mission)
    except ExperimentNotFoundError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/hardware/{hardware_id}", response_model=MissionRelevanceAssessment)
def get_hardware_mission_relevance(hardware_id: str, mission: str = Query(...), service: MissionRelevanceService = Depends(get_service)):
    try:
        return service.assess_hardware(hardware_id, mission)
    except HardwareNotFoundError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
