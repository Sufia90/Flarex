import json
import logging
import os
import tempfile
from pathlib import Path
from app.core.config import get_settings
from app.schemas.experiment import Experiment

logger = logging.getLogger(__name__)


class DuplicateExperimentError(ValueError):
    pass


class ExperimentNotFoundError(KeyError):
    pass


class ExperimentRepository:
    def __init__(self, data_dir: Path | None = None):
        if data_dir is None:
            data_dir = get_settings().data_path / "experiments"
        self.data_dir = Path(data_dir)
        self._experiments: list[Experiment] | None = None
        self._sources: dict[str, Path] = {}
        self._invalid_records: list[dict] = []

    @property
    def store_file(self) -> Path:
        return self.data_dir / "experiments.json"

    def _load_file(self, file_path: Path) -> list[Experiment]:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("Skipping experiment file %s: %s", file_path.name, exc)
            self._invalid_records.append({"file": str(file_path), "record_id": None, "record": None, "error": str(exc)})
            return []
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            logger.warning("Skipping experiment file %s: expected a list", file_path.name)
            self._invalid_records.append({"file": str(file_path), "record_id": None, "record": None, "error": "expected a list"})
            return []
        experiments = []
        for record in data:
            try:
                experiments.append(Experiment.model_validate(record))
            except Exception as exc:
                record_id = record.get("id") if isinstance(record, dict) else None
                logger.warning("Skipping invalid experiment record %s in %s: %s", record_id, file_path.name, exc)
                self._invalid_records.append({"file": str(file_path), "record_id": record_id, "record": record, "error": str(exc)})
        return experiments

    def _read_records(self, file_path: Path) -> list[Experiment]:
        if not file_path.is_file():
            return []
        return self._load_file(file_path)

    def _write_records(self, file_path: Path, experiments: list[Experiment]) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        data = [experiment.model_dump(mode="json") for experiment in experiments]
        fd, temp_name = tempfile.mkstemp(dir=str(file_path.parent), prefix=file_path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            os.replace(temp_name, file_path)
        except BaseException:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def _read_raw_list(self, file_path: Path) -> list:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        if isinstance(data, dict):
            return [data]
        return data if isinstance(data, list) else []

    def _write_raw_list(self, file_path: Path, records: list) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(dir=str(file_path.parent), prefix=file_path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(records, handle, indent=2)
            os.replace(temp_name, file_path)
        except BaseException:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def load(self) -> list[Experiment]:
        experiments = []
        self._sources = {}
        self._invalid_records = []
        if not self.data_dir.is_dir():
            self._experiments = []
            return []
        for file_path in sorted(self.data_dir.glob("*.json")):
            for experiment in self._load_file(file_path):
                if experiment.id in self._sources:
                    logger.warning("Skipping duplicate experiment id %s in %s", experiment.id, file_path.name)
                    self._invalid_records.append({"file": str(file_path), "record_id": experiment.id, "record": None, "error": "duplicate experiment id"})
                    continue
                self._sources[experiment.id] = file_path
                experiments.append(experiment)
        self._experiments = experiments
        return list(experiments)

    def get_all(self) -> list[Experiment]:
        if self._experiments is None:
            return self.load()
        return list(self._experiments)

    def get_invalid_records(self) -> list[dict]:
        if self._experiments is None:
            self.load()
        return list(self._invalid_records)

    def get_by_id(self, experiment_id: str) -> Experiment | None:
        wanted = experiment_id.strip().lower()
        for experiment in self.get_all():
            values = [experiment.id, experiment.nasa_investigation_id, experiment.acronym]
            for value in values:
                if value and value.lower() == wanted:
                    return experiment
        return None

    def reload(self) -> list[Experiment]:
        self._experiments = None
        return self.load()

    def create(self, experiment: Experiment) -> Experiment:
        if self.get_by_id(experiment.id) is not None:
            raise DuplicateExperimentError(experiment.id)
        stored = self._read_raw_list(self.store_file)
        stored.append(experiment.model_dump(mode="json"))
        self._write_raw_list(self.store_file, stored)
        self._sources[experiment.id] = self.store_file
        if self._experiments is None:
            self._experiments = []
        self._experiments.append(experiment)
        return experiment

    def update(self, experiment_id: str, experiment: Experiment) -> Experiment:
        if self.get_by_id(experiment_id) is None:
            raise ExperimentNotFoundError(experiment_id)
        updated = experiment.model_copy(update={"id": experiment_id})
        source = self._sources.get(experiment_id)
        if source is None:
            source = self.store_file
        records = self._read_raw_list(source)
        replaced = False
        new_records = []
        for record in records:
            if isinstance(record, dict) and record.get("id") == experiment_id:
                new_records.append(updated.model_dump(mode="json"))
                replaced = True
            else:
                new_records.append(record)
        if not replaced:
            new_records.append(updated.model_dump(mode="json"))
            source = self.store_file
        self._write_raw_list(source, new_records)
        self._sources[experiment_id] = source
        if self._experiments is not None:
            self._experiments = [updated if item.id == experiment_id else item for item in self._experiments]
        return updated

    def delete(self, experiment_id: str) -> None:
        if self.get_by_id(experiment_id) is None:
            raise ExperimentNotFoundError(experiment_id)
        source = self._sources.get(experiment_id)
        if source is None:
            return
        records = [record for record in self._read_raw_list(source) if not (isinstance(record, dict) and record.get("id") == experiment_id)]
        self._write_raw_list(source, records)
        del self._sources[experiment_id]
        if self._experiments is not None:
            self._experiments = [item for item in self._experiments if item.id != experiment_id]

    def search(self, filters: dict | None = None) -> list[Experiment]:
        filters = filters or {}
        query = str(filters.get("query") or filters.get("name") or "").strip().lower()
        research_category = filters.get("research_category")
        fuel_material = filters.get("fuel_material")
        hardware_id = filters.get("hardware_id")
        gravity_condition = filters.get("gravity_condition")
        mission_applicability = filters.get("mission_applicability")
        fire_safety_relevance = filters.get("fire_safety_relevance")
        data_completeness = filters.get("data_completeness")
        if isinstance(mission_applicability, str):
            mission_applicability = [mission_applicability]
        if isinstance(fire_safety_relevance, str):
            fire_safety_relevance = [fire_safety_relevance]
        results = []
        for experiment in self.get_all():
            if query:
                haystack = " ".join(
                    [
                        experiment.id or "",
                        experiment.nasa_investigation_id or "",
                        experiment.name or "",
                        experiment.acronym or "",
                        experiment.description or "",
                        experiment.scientific_objective or "",
                        experiment.research_category or "",
                        experiment.fuel_material or "",
                    ]
                ).lower()
                if query not in haystack:
                    continue
            if research_category and (experiment.research_category or "").lower() != str(research_category).lower():
                continue
            if fuel_material and str(fuel_material).lower() not in (experiment.fuel_material or "").lower():
                continue
            if hardware_id and hardware_id not in experiment.hardware_ids:
                continue
            if gravity_condition:
                conditions = experiment.conditions
                if conditions is None or (conditions.gravity_condition or "").lower() != str(gravity_condition).lower():
                    continue
            if mission_applicability and not any(value in experiment.mission_applicability for value in mission_applicability):
                continue
            if fire_safety_relevance and not any(value in experiment.fire_safety_relevance for value in fire_safety_relevance):
                continue
            if data_completeness:
                completeness = experiment.data_quality.completeness
                completeness_value = getattr(completeness, "value", completeness)
                if str(completeness_value).lower() != str(data_completeness).lower():
                    continue
            results.append(experiment)
        return results
