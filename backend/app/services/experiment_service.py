from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment
from app.schemas.response import PaginatedExperimentList
from app.services.relationship_service import ReferencedByRelationshipError


class ExperimentService:
    def __init__(self, repository: ExperimentRepository | None = None, relationship_repository: RelationshipRepository | None = None):
        self.repository = repository or ExperimentRepository()
        self.relationship_repository = relationship_repository or RelationshipRepository()

    def _validate_id(self, experiment_id: str) -> str:
        cleaned = (experiment_id or "").strip()
        if not cleaned:
            raise ValueError("experiment_id must not be empty")
        return cleaned

    def _validate_pagination(self, page: int, page_size: int) -> None:
        if page < 1:
            raise ValueError("page must be at least 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")

    def _paginate(self, items: list[Experiment], page: int, page_size: int) -> PaginatedExperimentList:
        self._validate_pagination(page, page_size)
        total = len(items)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start = (page - 1) * page_size
        end = start + page_size
        return PaginatedExperimentList(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items[start:end],
        )

    def create_experiment(self, experiment: Experiment) -> Experiment:
        self._validate_id(experiment.id)
        return self.repository.create(experiment)

    def get_experiment(self, experiment_id: str) -> Experiment:
        cleaned = self._validate_id(experiment_id)
        experiment = self.repository.get_by_id(cleaned)
        if experiment is None:
            from app.repositories.experiment_repository import ExperimentNotFoundError
            raise ExperimentNotFoundError(cleaned)
        return experiment

    def list_experiments(self, page: int = 1, page_size: int = 20) -> PaginatedExperimentList:
        return self._paginate(self.repository.get_all(), page, page_size)

    def search_experiments(self, filters: dict | None = None, page: int = 1, page_size: int = 20) -> PaginatedExperimentList:
        return self._paginate(self.repository.search(filters), page, page_size)

    def update_experiment(self, experiment_id: str, experiment: Experiment) -> Experiment:
        cleaned = self._validate_id(experiment_id)
        return self.repository.update(cleaned, experiment)

    def delete_experiment(self, experiment_id: str) -> None:
        cleaned = self._validate_id(experiment_id)
        experiment = self.repository.get_by_id(cleaned)
        if experiment is not None and self.relationship_repository.get_by_experiment_id(experiment.id):
            raise ReferencedByRelationshipError(experiment.id)
        self.repository.delete(cleaned)
