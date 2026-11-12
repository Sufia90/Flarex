from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.experiment_repository import ExperimentNotFoundError
from app.repositories.hardware_repository import HardwareNotFoundError
from app.schemas.fire_safety import FireSafetyCategory, FireSafetyEvidenceStatus, FireSafetyInsight, FireSafetySummary
from app.schemas.response import PaginatedFireSafetyInsightList
from app.services.fire_safety_service import FireSafetyService

router = APIRouter(prefix="/v1/fire-safety", tags=["fire-safety"])


def get_service() -> FireSafetyService:
    return FireSafetyService()


def _paginate(insights: list[FireSafetyInsight], page: int, page_size: int) -> PaginatedFireSafetyInsightList:
    total = len(insights)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedFireSafetyInsightList(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=insights[start:end],
    )


@router.get("/insights", response_model=PaginatedFireSafetyInsightList)
def list_insights(
    service: FireSafetyService = Depends(get_service),
    category: FireSafetyCategory | None = None,
    evidence_status: FireSafetyEvidenceStatus | None = None,
    experiment_id: str | None = None,
    hardware_id: str | None = None,
    mission: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    try:
        insights = service.search_insights(
            category=category,
            experiment_id=experiment_id,
            hardware_id=hardware_id,
            evidence_status=evidence_status,
            mission=mission,
        )
    except ExperimentNotFoundError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    except HardwareNotFoundError:
        raise HTTPException(status_code=404, detail="Hardware not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _paginate(insights, page, page_size)


@router.get("/prevention", response_model=PaginatedFireSafetyInsightList)
def list_prevention_insights(
    service: FireSafetyService = Depends(get_service),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    insights = service.get_insights_by_category(FireSafetyCategory.PREVENTION)
    return _paginate(insights, page, page_size)


@router.get("/detection", response_model=PaginatedFireSafetyInsightList)
def list_detection_insights(
    service: FireSafetyService = Depends(get_service),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    insights = service.get_insights_by_category(FireSafetyCategory.DETECTION)
    return _paginate(insights, page, page_size)


@router.get("/suppression", response_model=PaginatedFireSafetyInsightList)
def list_suppression_insights(
    service: FireSafetyService = Depends(get_service),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    insights = service.get_insights_by_category(FireSafetyCategory.SUPPRESSION)
    return _paginate(insights, page, page_size)


@router.get("/summary", response_model=FireSafetySummary)
def get_summary(service: FireSafetyService = Depends(get_service)):
    return service.get_summary()


@router.get("/experiments/{experiment_id}", response_model=list[FireSafetyInsight])
def list_experiment_insights(
    experiment_id: str,
    service: FireSafetyService = Depends(get_service),
    category: FireSafetyCategory | None = None,
    evidence_status: FireSafetyEvidenceStatus | None = None,
):
    try:
        insights = service.get_insights_for_experiment(experiment_id)
    except ExperimentNotFoundError:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if category is not None:
        insights = [insight for insight in insights if insight.category == category]
    if evidence_status is not None:
        insights = [insight for insight in insights if insight.evidence_status == evidence_status]
    return insights


@router.get("/hardware/{hardware_id}", response_model=list[FireSafetyInsight])
def list_hardware_insights(
    hardware_id: str,
    service: FireSafetyService = Depends(get_service),
):
    try:
        return service.get_insights_for_hardware(hardware_id)
    except HardwareNotFoundError:
        raise HTTPException(status_code=404, detail="Hardware not found")
