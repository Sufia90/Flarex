from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.hardware import Hardware
from app.schemas.response import PaginatedHardwareList
from app.services.relationship_service import ReferencedByRelationshipError


class HardwareService:
    def __init__(self, repository: HardwareRepository | None = None, relationship_repository: RelationshipRepository | None = None):
        self.repository = repository or HardwareRepository()
        self.relationship_repository = relationship_repository or RelationshipRepository()

    def _validate_id(self, hardware_id: str) -> str:
        cleaned = (hardware_id or "").strip()
        if not cleaned:
            raise ValueError("hardware_id must not be empty")
        return cleaned

    def _validate_pagination(self, page: int, page_size: int) -> None:
        if page < 1:
            raise ValueError("page must be at least 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")

    def _paginate(self, items: list[Hardware], page: int, page_size: int) -> PaginatedHardwareList:
        self._validate_pagination(page, page_size)
        total = len(items)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start = (page - 1) * page_size
        end = start + page_size
        return PaginatedHardwareList(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items[start:end],
        )

    def create_hardware(self, hardware: Hardware) -> Hardware:
        self._validate_id(hardware.id)
        return self.repository.create(hardware)

    def get_hardware(self, hardware_id: str) -> Hardware:
        cleaned = self._validate_id(hardware_id)
        hardware = self.repository.get_by_id(cleaned)
        if hardware is None:
            raise HardwareNotFoundError(cleaned)
        return hardware

    def list_hardware(self, page: int = 1, page_size: int = 20) -> PaginatedHardwareList:
        return self._paginate(self.repository.get_all(), page, page_size)

    def search_hardware(self, filters: dict | None = None, page: int = 1, page_size: int = 20) -> PaginatedHardwareList:
        return self._paginate(self.repository.search(filters), page, page_size)

    def update_hardware(self, hardware_id: str, hardware: Hardware) -> Hardware:
        cleaned = self._validate_id(hardware_id)
        return self.repository.update(cleaned, hardware)

    def delete_hardware(self, hardware_id: str) -> None:
        cleaned = self._validate_id(hardware_id)
        hardware = self.repository.get_by_id(cleaned)
        if hardware is not None and self.relationship_repository.get_by_hardware_id(hardware.id):
            raise ReferencedByRelationshipError(hardware.id)
        self.repository.delete(cleaned)
