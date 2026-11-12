import json
import logging
import os
import tempfile
from pathlib import Path
from pydantic import ValidationError
from app.core.config import get_settings
from app.schemas.relationship import ExperimentHardwareRelationship

logger = logging.getLogger("nasa-combustion-explorer")


class DuplicateRelationshipError(ValueError):
    pass


class RelationshipNotFoundError(KeyError):
    pass


class DuplicateRelationshipReferenceError(ValueError):
    pass


class RelationshipRepository:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or get_settings().data_path / "relationships"
        self._relationships: list[ExperimentHardwareRelationship] = []
        self._sources: dict[str, Path] = {}
        self._invalid_records: list[dict] = []
        self.load()

    def load(self) -> None:
        self._relationships = []
        self._sources = {}
        self._invalid_records = []
        if not self.data_dir.exists():
            return
        for file in sorted(self.data_dir.glob("*.json")):
            self._load_file(file)

    def _load_file(self, file: Path) -> None:
        try:
            with open(file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipped unreadable relationship file %s: %s", file, exc)
            self._invalid_records.append({"file": str(file), "record_id": None, "record": None, "error": str(exc)})
            return
        if not isinstance(data, list):
            logger.warning("Skipped relationship file %s: expected a list of records", file)
            self._invalid_records.append({"file": str(file), "record_id": None, "record": None, "error": "expected a list of records"})
            return
        for record in data:
            if not isinstance(record, dict):
                logger.warning("Skipped invalid relationship record in %s: not an object", file)
                self._invalid_records.append({"file": str(file), "record_id": None, "record": record, "error": "not an object"})
                continue
            record_id = record.get("id")
            try:
                relationship = ExperimentHardwareRelationship.model_validate(record)
            except ValidationError as exc:
                logger.warning("Skipped invalid relationship record %s in %s: %s", record_id, file, exc)
                self._invalid_records.append({"file": str(file), "record_id": record_id, "record": record, "error": str(exc)})
                continue
            if relationship.id in self._sources:
                logger.warning("Skipped duplicate relationship id %s in %s", relationship.id, file)
                self._invalid_records.append({"file": str(file), "record_id": relationship.id, "record": record, "error": "duplicate relationship id"})
                continue
            if self._find_link(relationship.experiment_id, relationship.hardware_id, relationship.relationship_type.value) is not None:
                logger.warning("Skipped duplicate relationship link %s %s %s in %s", relationship.experiment_id, relationship.hardware_id, relationship.relationship_type.value, file)
                self._invalid_records.append({"file": str(file), "record_id": relationship.id, "record": record, "error": "duplicate relationship link"})
                continue
            self._relationships.append(relationship)
            self._sources[relationship.id] = file

    def _read_raw_list(self, file: Path) -> list:
        try:
            with open(file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError):
            return []
        return data if isinstance(data, list) else []

    def _write_raw_list(self, file: Path, records: list) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=file.parent, suffix=".tmp", delete=False)
        try:
            json.dump(records, handle, indent=2)
            handle.close()
            os.replace(handle.name, file)
        except Exception:
            try:
                handle.close()
            except Exception:
                pass
            try:
                os.unlink(handle.name)
            except OSError:
                pass
            raise

    def reload(self) -> None:
        self.load()

    def get_all(self) -> list[ExperimentHardwareRelationship]:
        return list(self._relationships)

    def get_invalid_records(self) -> list[dict]:
        return list(self._invalid_records)

    def get_by_id(self, relationship_id: str) -> ExperimentHardwareRelationship | None:
        cleaned = (relationship_id or "").strip().lower()
        if not cleaned:
            return None
        for relationship in self._relationships:
            if relationship.id.lower() == cleaned:
                return relationship
        return None

    def get_by_experiment_id(self, experiment_id: str) -> list[ExperimentHardwareRelationship]:
        cleaned = (experiment_id or "").strip().lower()
        return [item for item in self._relationships if item.experiment_id.lower() == cleaned]

    def get_by_hardware_id(self, hardware_id: str) -> list[ExperimentHardwareRelationship]:
        cleaned = (hardware_id or "").strip().lower()
        return [item for item in self._relationships if item.hardware_id.lower() == cleaned]

    def _find_link(self, experiment_id: str, hardware_id: str, relationship_type: str) -> ExperimentHardwareRelationship | None:
        experiment_cleaned = (experiment_id or "").strip().lower()
        hardware_cleaned = (hardware_id or "").strip().lower()
        type_cleaned = (relationship_type or "").strip().lower()
        for item in self._relationships:
            if (
                item.experiment_id.lower() == experiment_cleaned
                and item.hardware_id.lower() == hardware_cleaned
                and item.relationship_type.value.lower() == type_cleaned
            ):
                return item
        return None

    def create(self, relationship: ExperimentHardwareRelationship) -> ExperimentHardwareRelationship:
        if self.get_by_id(relationship.id) is not None:
            raise DuplicateRelationshipError(relationship.id)
        if self._find_link(relationship.experiment_id, relationship.hardware_id, relationship.relationship_type.value) is not None:
            raise DuplicateRelationshipReferenceError(relationship.experiment_id + " " + relationship.hardware_id + " " + relationship.relationship_type.value)
        store_file = self.data_dir / "experiment_hardware.json"
        records = self._read_raw_list(store_file) if store_file.exists() else []
        records.append(relationship.model_dump(mode="json"))
        self._write_raw_list(store_file, records)
        self._relationships.append(relationship)
        self._sources[relationship.id] = store_file
        return relationship

    def update(self, relationship_id: str, relationship: ExperimentHardwareRelationship) -> ExperimentHardwareRelationship:
        existing = self.get_by_id(relationship_id)
        if existing is None:
            raise RelationshipNotFoundError(relationship_id)
        updated = relationship.model_copy(update={"id": existing.id})
        other = self._find_link(updated.experiment_id, updated.hardware_id, updated.relationship_type.value)
        if other is not None and other.id != existing.id:
            raise DuplicateRelationshipReferenceError(updated.experiment_id + " " + updated.hardware_id + " " + updated.relationship_type.value)
        source = self._sources[existing.id]
        records = self._read_raw_list(source)
        replaced = False
        for index, record in enumerate(records):
            if isinstance(record, dict) and str(record.get("id", "")).strip() == existing.id:
                records[index] = updated.model_dump(mode="json")
                replaced = True
                break
        if not replaced:
            records.append(updated.model_dump(mode="json"))
        self._write_raw_list(source, records)
        for index, item in enumerate(self._relationships):
            if item.id == existing.id:
                self._relationships[index] = updated
                break
        return updated

    def delete(self, relationship_id: str) -> None:
        existing = self.get_by_id(relationship_id)
        if existing is None:
            raise RelationshipNotFoundError(relationship_id)
        source = self._sources[existing.id]
        records = self._read_raw_list(source)
        kept = [record for record in records if not (isinstance(record, dict) and str(record.get("id", "")).strip() == existing.id)]
        self._write_raw_list(source, kept)
        self._relationships = [item for item in self._relationships if item.id != existing.id]
        del self._sources[existing.id]

    def search(self, filters: dict | None = None) -> list[ExperimentHardwareRelationship]:
        if not filters:
            return self.get_all()
        results = self.get_all()
        query = filters.get("query")
        if query:
            needle = str(query).strip().lower()
            results = [
                item
                for item in results
                if needle in item.id.lower()
                or needle in item.experiment_id.lower()
                or needle in item.hardware_id.lower()
                or (item.role and needle in item.role.lower())
                or (item.evidence and needle in item.evidence.lower())
                or (item.notes and needle in item.notes.lower())
            ]
        experiment_id = filters.get("experiment_id")
        if experiment_id:
            wanted = str(experiment_id).strip().lower()
            results = [item for item in results if item.experiment_id.lower() == wanted]
        hardware_id = filters.get("hardware_id")
        if hardware_id:
            wanted = str(hardware_id).strip().lower()
            results = [item for item in results if item.hardware_id.lower() == wanted]
        relationship_type = filters.get("relationship_type")
        if relationship_type:
            wanted = str(relationship_type).strip().lower()
            results = [item for item in results if item.relationship_type.value.lower() == wanted]
        verification_status = filters.get("verification_status")
        if verification_status:
            wanted = str(verification_status).strip().lower()
            results = [item for item in results if item.verification_status.value.lower() == wanted]
        role = filters.get("role")
        if role:
            needle = str(role).strip().lower()
            results = [item for item in results if item.role and needle in item.role.lower()]
        return results
