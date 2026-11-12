from app.repositories.source_repository import SourceNotFoundError, SourceRepository
from app.schemas.common import VerificationStatus
from app.schemas.relationship import Source
from app.schemas.response import PaginatedSourceList


class SourceService:
    def __init__(self, repository=None):
        self.repository = repository or SourceRepository()

    def _validate_id(self, source_id):
        if source_id is None or str(source_id).strip() == "":
            raise ValueError("source id must not be empty")

    def _validate_pagination(self, page, page_size):
        if page < 1:
            raise ValueError("page must be at least 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")

    def _paginate(self, items, page, page_size):
        total = len(items)
        if total == 0:
            total_pages = 0
        else:
            total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        page_items = items[start:start + page_size]
        return PaginatedSourceList(total=total, page=page, page_size=page_size, total_pages=total_pages, items=page_items)

    def create_source(self, source: Source):
        self._validate_id(source.id)
        return self.repository.create(source)

    def get_source(self, source_id: str):
        self._validate_id(source_id)
        found = self.repository.get_by_id(source_id)
        if found is None:
            raise SourceNotFoundError(source_id)
        return found

    def list_sources(self, page=1, page_size=20):
        self._validate_pagination(page, page_size)
        return self._paginate(self.repository.get_all(), page, page_size)

    def search_sources(self, filters, page=1, page_size=20):
        self._validate_pagination(page, page_size)
        return self._paginate(self.repository.search(filters or {}), page, page_size)

    def update_source(self, source_id: str, source: Source):
        self._validate_id(source_id)
        return self.repository.update(source_id, source)

    def delete_source(self, source_id: str):
        self._validate_id(source_id)
        return self.repository.delete(source_id)

    def set_verification_status(self, source_id: str, status):
        self._validate_id(source_id)
        if isinstance(status, str):
            status = VerificationStatus(status)
        existing = self.get_source(source_id)
        updated = existing.model_copy(update={"verification_status": status})
        return self.repository.update(source_id, updated)
