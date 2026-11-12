from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.repositories.source_repository import DuplicateSourceError, SourceNotFoundError
from app.schemas.common import VerificationStatus
from app.schemas.relationship import Source, SourceType
from app.schemas.response import DeleteResponse, PaginatedSourceList
from app.services.source_service import SourceService


class VerificationStatusRequest(BaseModel):
    verification_status: VerificationStatus


router = APIRouter(prefix="/v1/sources", tags=["sources"])


def get_service():
    return SourceService()


@router.post("", response_model=Source, status_code=201)
def create_source(source: Source, service: SourceService = Depends(get_service)):
    try:
        return service.create_source(source)
    except DuplicateSourceError:
        raise HTTPException(status_code=409, detail="Source already exists")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=PaginatedSourceList)
def list_sources(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), service: SourceService = Depends(get_service)):
    try:
        return service.list_sources(page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/search", response_model=PaginatedSourceList)
def search_sources(
    query: str | None = None,
    source_type: SourceType | None = None,
    verification_status: VerificationStatus | None = None,
    nasa_report_id: str | None = None,
    publisher: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: SourceService = Depends(get_service),
):
    try:
        filters = {"query": query, "source_type": source_type, "verification_status": verification_status, "nasa_report_id": nasa_report_id, "publisher": publisher}
        return service.search_sources(filters, page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{source_id}", response_model=Source)
def get_source(source_id: str, service: SourceService = Depends(get_service)):
    try:
        return service.get_source(source_id)
    except SourceNotFoundError:
        raise HTTPException(status_code=404, detail="Source not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{source_id}", response_model=Source)
def update_source(source_id: str, source: Source, service: SourceService = Depends(get_service)):
    try:
        return service.update_source(source_id, source)
    except SourceNotFoundError:
        raise HTTPException(status_code=404, detail="Source not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{source_id}", response_model=DeleteResponse)
def delete_source(source_id: str, service: SourceService = Depends(get_service)):
    try:
        deleted = service.delete_source(source_id)
        return DeleteResponse(message="Source deleted", deleted_id=deleted.id)
    except SourceNotFoundError:
        raise HTTPException(status_code=404, detail="Source not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{source_id}/verification", response_model=Source)
def set_verification(source_id: str, body: VerificationStatusRequest, service: SourceService = Depends(get_service)):
    try:
        return service.set_verification_status(source_id, body.verification_status)
    except SourceNotFoundError:
        raise HTTPException(status_code=404, detail="Source not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
