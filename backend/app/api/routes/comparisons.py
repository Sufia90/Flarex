from fastapi import APIRouter, Depends, HTTPException

from app.repositories.experiment_repository import ExperimentNotFoundError
from app.repositories.hardware_repository import HardwareNotFoundError
from app.schemas.comparison import (
    ExperimentComparison,
    ExperimentComparisonRequest,
    HardwareComparison,
    HardwareComparisonRequest,
    MeasurementComparison,
    MeasurementComparisonRequest,
)
from app.services.comparison_service import ComparisonService, MeasurementNotFoundError

router = APIRouter(prefix="/v1/comparisons", tags=["comparisons"])


def get_service() -> ComparisonService:
    return ComparisonService()


@router.post("/experiments", response_model=ExperimentComparison)
def compare_experiments(request: ExperimentComparisonRequest, service: ComparisonService = Depends(get_service)):
    try:
        return service.compare_experiments(request.experiment_ids, request.parameters, request.include_conditions)
    except ExperimentNotFoundError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/hardware", response_model=HardwareComparison)
def compare_hardware(request: HardwareComparisonRequest, service: ComparisonService = Depends(get_service)):
    try:
        return service.compare_hardware(request.hardware_ids, request.fields)
    except HardwareNotFoundError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/measurements", response_model=MeasurementComparison)
def compare_measurements(request: MeasurementComparisonRequest, service: ComparisonService = Depends(get_service)):
    try:
        return service.compare_measurements(request.measurement_ids, request.parameter_names)
    except MeasurementNotFoundError:
        raise HTTPException(status_code=404, detail="Measurement not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
