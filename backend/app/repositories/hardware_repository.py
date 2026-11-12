import json
import logging
import os
import tempfile
from pathlib import Path
from pydantic import ValidationError
from app.core.config import get_settings
from app.schemas.hardware import Hardware

logger = logging.getLogger("nasa-combustion-explorer")


class DuplicateHardwareError(ValueError):
    pass


class HardwareNotFoundError(KeyError):
    pass


class HardwareRepository:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or get_settings().data_path / "hardware"
        self._hardware: list[Hardware] = []
        self._sources: dict[str, Path] = {}
        self._invalid_records: list[dict] = []
        self.load()

    def load(self) -> None:
        self._hardware = []
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
            logger.warning("Skipped unreadable hardware file %s: %s", file, exc)
            self._invalid_records.append({"file": str(file), "record_id": None, "record": None, "error": str(exc)})
            return
        if not isinstance(data, list):
            logger.warning("Skipped hardware file %s: expected a list of records", file)
            self._invalid_records.append({"file": str(file), "record_id": None, "record": None, "error": "expected a list of records"})
            return
        for record in data:
            if not isinstance(record, dict):
                logger.warning("Skipped invalid hardware record in %s: not an object", file)
                self._invalid_records.append({"file": str(file), "record_id": None, "record": record, "error": "not an object"})
                continue
            record_id = record.get("id")
            try:
                hardware = Hardware.model_validate(record)
            except ValidationError as exc:
                logger.warning("Skipped invalid hardware record %s in %s: %s", record_id, file, exc)
                self._invalid_records.append({"file": str(file), "record_id": record_id, "record": record, "error": str(exc)})
                continue
            if hardware.id in self._sources:
                logger.warning("Skipped duplicate hardware id %s in %s", hardware.id, file)
                self._invalid_records.append({"file": str(file), "record_id": hardware.id, "record": record, "error": "duplicate hardware id"})
                continue
            self._hardware.append(hardware)
            self._sources[hardware.id] = file

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

    def get_all(self) -> list[Hardware]:
        return list(self._hardware)

    def get_invalid_records(self) -> list[dict]:
        return list(self._invalid_records)

    def get_by_id(self, hardware_id: str) -> Hardware | None:
        cleaned = (hardware_id or "").strip().lower()
        if not cleaned:
            return None
        for hardware in self._hardware:
            if hardware.id.lower() == cleaned:
                return hardware
            if hardware.acronym and hardware.acronym.lower() == cleaned:
                return hardware
        return None

    def create(self, hardware: Hardware) -> Hardware:
        if self.get_by_id(hardware.id) is not None:
            raise DuplicateHardwareError(hardware.id)
        store_file = self.data_dir / "hardware.json"
        records = self._read_raw_list(store_file) if store_file.exists() else []
        records.append(hardware.model_dump(mode="json"))
        self._write_raw_list(store_file, records)
        self._hardware.append(hardware)
        self._sources[hardware.id] = store_file
        return hardware

    def update(self, hardware_id: str, hardware: Hardware) -> Hardware:
        existing = self.get_by_id(hardware_id)
        if existing is None:
            raise HardwareNotFoundError(hardware_id)
        updated = hardware.model_copy(update={"id": existing.id})
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
        for index, item in enumerate(self._hardware):
            if item.id == existing.id:
                self._hardware[index] = updated
                break
        return updated

    def delete(self, hardware_id: str) -> None:
        existing = self.get_by_id(hardware_id)
        if existing is None:
            raise HardwareNotFoundError(hardware_id)
        source = self._sources[existing.id]
        records = self._read_raw_list(source)
        kept = [record for record in records if not (isinstance(record, dict) and str(record.get("id", "")).strip() == existing.id)]
        self._write_raw_list(source, kept)
        self._hardware = [item for item in self._hardware if item.id != existing.id]
        del self._sources[existing.id]

    def search(self, filters: dict | None = None) -> list[Hardware]:
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
                or needle in item.name.lower()
                or (item.acronym and needle in item.acronym.lower())
                or (item.description and needle in item.description.lower())
                or (item.purpose and needle in item.purpose.lower())
                or (item.facility_classification and needle in item.facility_classification.lower())
            ]
        name = filters.get("name")
        if name:
            needle = str(name).strip().lower()
            results = [item for item in results if needle in item.name.lower()]
        hardware_type = filters.get("hardware_type")
        if hardware_type:
            wanted = str(hardware_type).strip().lower()
            results = [item for item in results if item.hardware_type.value.lower() == wanted]
        parent_hardware_id = filters.get("parent_hardware_id")
        if parent_hardware_id:
            wanted = str(parent_hardware_id).strip().lower()
            results = [item for item in results if item.parent_hardware_id and item.parent_hardware_id.lower() == wanted]
        facility_classification = filters.get("facility_classification")
        if facility_classification:
            wanted = str(facility_classification).strip().lower()
            results = [item for item in results if item.facility_classification and item.facility_classification.lower() == wanted]
        supported_measurements = filters.get("supported_measurements")
        if supported_measurements:
            wanted = [supported_measurements] if isinstance(supported_measurements, str) else list(supported_measurements)
            wanted = [str(value).strip().lower() for value in wanted]
            results = [item for item in results if any(value.lower() in wanted for value in item.supported_measurements)]
        related_experiment_ids = filters.get("related_experiment_ids")
        if related_experiment_ids:
            wanted = [related_experiment_ids] if isinstance(related_experiment_ids, str) else list(related_experiment_ids)
            wanted = [str(value).strip().lower() for value in wanted]
            results = [item for item in results if any(value.lower() in wanted for value in item.related_experiment_ids)]
        return results
