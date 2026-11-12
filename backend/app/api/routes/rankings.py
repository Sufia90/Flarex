from fastapi import APIRouter, Depends, HTTPException

from app.repositories.experiment_repository import ExperimentNotFoundError
from app.repositories.hardware_repository import HardwareNotFoundError
from app.schemas.ranking import RankingRequest, RankingResult
from app.services.ranking_service import RankingService

router = APIRouter(prefix="/v1/rankings", tags=["rankings"])


def get_service() -> RankingService:
    return RankingService()


@router.post("", response_model=RankingResult)
def create_ranking(request: RankingRequest, service: RankingService = Depends(get_service)):
    try:
        return service.rank(request)
    except ExperimentNotFoundError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except HardwareNotFoundError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
