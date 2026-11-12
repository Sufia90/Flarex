from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.repositories.relationship_repository import RelationshipNotFoundError, RelationshipRepository
from app.schemas.relationship import ExperimentHardwareRelationship
from app.schemas.response import PaginatedRelationshipList


class InvalidExperimentReferenceError(ValueError):
    pass


class InvalidHardwareReferenceError(ValueError):
    pass


class ReferencedByRelationshipError(ValueError):
    pass


class RelationshipService:
    def __init__(
        self,
        repository: RelationshipRepository | None = None,
        experiment_repository: ExperimentRepository | None = None,
        hardware_repository: HardwareRepository | None = None,
    ):
        self.repository = repository or RelationshipRepository()
        self.experiment_repository = experiment_repository or ExperimentRepository()
        self.hardware_repository = hardware_repository or HardwareRepository()

    def _validate_id(self, relationship_id: str) -> str:
        cleaned = (relationship_id or "").strip()
        if not cleaned:
            raise ValueError("relationship_id must not be empty")
        return cleaned

    def _validate_reference(self, experiment_id: str, hardware_id: str) -> None:
        if self.experiment_repository.get_by_id(experiment_id) is None:
            raise InvalidExperimentReferenceError(experiment_id)
        if self.hardware_repository.get_by_id(hardware_id) is None:
            raise InvalidHardwareReferenceError(hardware_id)

    def _validate_pagination(self, page: int, page_size: int) -> None:
        if page < 1:
            raise ValueError("page must be at least 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")

    def _paginate(self, items: list[ExperimentHardwareRelationship], page: int, page_size: int) -> PaginatedRelationshipList:
        self._validate_pagination(page, page_size)
        total = len(items)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start = (page - 1) * page_size
        end = start + page_size
        return PaginatedRelationshipList(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items[start:end],
        )

    def create_relationship(self, relationship: ExperimentHardwareRelationship) -> ExperimentHardwareRelationship:
        self._validate_id(relationship.id)
        self._validate_reference(relationship.experiment_id, relationship.hardware_id)
        return self.repository.create(relationship)

    def get_relationship(self, relationship_id: str) -> ExperimentHardwareRelationship:
        cleaned = self._validate_id(relationship_id)
        relationship = self.repository.get_by_id(cleaned)
        if relationship is None:
            raise RelationshipNotFoundError(cleaned)
        return relationship

    def list_relationships(self, page: int = 1, page_size: int = 20) -> PaginatedRelationshipList:
        return self._paginate(self.repository.get_all(), page, page_size)

    def get_by_experiment(self, experiment_id: str, page: int = 1, page_size: int = 20) -> PaginatedRelationshipList:
        cleaned = (experiment_id or "").strip()
        if self.experiment_repository.get_by_id(cleaned) is None:
            raise InvalidExperimentReferenceError(cleaned)
        return self._paginate(self.repository.get_by_experiment_id(cleaned), page, page_size)

    def get_by_hardware(self, hardware_id: str, page: int = 1, page_size: int = 20) -> PaginatedRelationshipList:
        cleaned = (hardware_id or "").strip()
        if self.hardware_repository.get_by_id(cleaned) is None:
            raise InvalidHardwareReferenceError(cleaned)
        return self._paginate(self.repository.get_by_hardware_id(cleaned), page, page_size)

    def search_relationships(self, filters: dict | None = None, page: int = 1, page_size: int = 20) -> PaginatedRelationshipList:
        return self._paginate(self.repository.search(filters), page, page_size)

    def update_relationship(self, relationship_id: str, relationship: ExperimentHardwareRelationship) -> ExperimentHardwareRelationship:
        cleaned = self._validate_id(relationship_id)
        existing = self.repository.get_by_id(cleaned)
        if existing is None:
            raise RelationshipNotFoundError(cleaned)
        self._validate_reference(relationship.experiment_id, relationship.hardware_id)
        return self.repository.update(cleaned, relationship)

    def delete_relationship(self, relationship_id: str) -> None:
        cleaned = self._validate_id(relationship_id)
        self.repository.delete(cleaned)

    def has_relationships_for_experiment(self, experiment_id: str) -> bool:
        return len(self.repository.get_by_experiment_id(experiment_id)) > 0

    def has_relationships_for_hardware(self, hardware_id: str) -> bool:
        return len(self.repository.get_by_hardware_id(hardware_id)) > 0
