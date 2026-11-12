import json
import logging
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.common import VerificationStatus
from app.schemas.relationship import Source, SourceType

logger = logging.getLogger("nasa-combustion-explorer")


class DuplicateSourceError(ValueError):
    pass


class SourceNotFoundError(KeyError):
    pass


class SourceRepository:
    def __init__(self, data_dir: Path | str | None = None):
        if data_dir is None:
            self.data_dir = get_settings().data_path / "sources"
        else:
            self.data_dir = Path(data_dir)
        self._sources: dict[str, Source] = {}
        self._sources_index: dict[str, Path] = {}
        self._invalid_records: list[dict] = []
        self.load()

    def load(self):
        self._sources = {}
        self._sources_index = {}
        self._invalid_records = []
        if not self.data_dir.exists():
            return
        for path in sorted(self.data_dir.glob("*.json")):
            self._load_file(path)

    def reload(self):
        self.load()

    def _load_file(self, path: Path):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, ValueError) as exc:
            logger.warning("Skipping source file %s: %s", path, exc)
            self._invalid_records.append({"file": str(path), "record_id": None, "record": None, "error": str(exc)})
            return
        if not isinstance(raw, list):
            logger.warning("Skipping source file %s: expected a list", path)
            self._invalid_records.append({"file": str(path), "record_id": None, "record": raw, "error": "expected a list"})
            return
        for record in raw:
            if not isinstance(record, dict):
                logger.warning("Skipping source record in %s: expected an object", path)
                self._invalid_records.append({"file": str(path), "record_id": None, "record": record, "error": "expected an object"})
                continue
            record_id = record.get("id")
            try:
                source = Source(**record)
            except ValidationError as exc:
                logger.warning("Skipping source record %s in %s: %s", record_id, path, exc)
                self._invalid_records.append({"file": str(path), "record_id": record_id, "record": record, "error": str(exc)})
                continue
            key = source.id.strip().lower()
            if key in self._sources:
                logger.warning("Skipping duplicate source id %s in %s", source.id, path)
                self._invalid_records.append({"file": str(path), "record_id": source.id, "record": record, "error": "duplicate id"})
                continue
            self._sources[key] = source
            self._sources_index[key] = path

    def _read_raw_list(self, path: Path):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except (OSError, ValueError):
            return []
        if not isinstance(raw, list):
            return []
        return raw

    def _write_raw_list(self, path: Path, records):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(records, handle, indent=2)
                handle.write("\n")
            os.replace(temp_name, path)
        except BaseException:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def get_all(self):
        return list(self._sources.values())

    def get_invalid_records(self):
        return list(self._invalid_records)

    def get_by_id(self, source_id: str):
        if source_id is None:
            return None
        return self._sources.get(str(source_id).strip().lower())

    def create(self, source: Source):
        key = source.id.strip().lower()
        if key in self._sources:
            raise DuplicateSourceError(f"Source with id {source.id} already exists")
        target = self.data_dir / "sources.json"
        raw = self._read_raw_list(target)
        raw.append(source.model_dump(mode="json"))
        self._write_raw_list(target, raw)
        self._sources[key] = source
        self._sources_index[key] = target
        return source

    def update(self, source_id: str, source: Source):
        existing = self.get_by_id(source_id)
        if existing is None:
            raise SourceNotFoundError(source_id)
        updated = source.model_copy(update={"id": existing.id})
        key = existing.id.strip().lower()
        target = self._sources_index.get(key, self.data_dir / "sources.json")
        raw = self._read_raw_list(target)
        replaced = False
        for index, record in enumerate(raw):
            if isinstance(record, dict) and str(record.get("id", "")).strip().lower() == key:
                raw[index] = updated.model_dump(mode="json")
                replaced = True
                break
        if not replaced:
            raw.append(updated.model_dump(mode="json"))
        self._write_raw_list(target, raw)
        self._sources[key] = updated
        self._sources_index[key] = target
        return updated

    def delete(self, source_id: str):
        existing = self.get_by_id(source_id)
        if existing is None:
            raise SourceNotFoundError(source_id)
        key = existing.id.strip().lower()
        target = self._sources_index.get(key, self.data_dir / "sources.json")
        raw = self._read_raw_list(target)
        raw = [record for record in raw if not (isinstance(record, dict) and str(record.get("id", "")).strip().lower() == key)]
        self._write_raw_list(target, raw)
        del self._sources[key]
        self._sources_index.pop(key, None)
        return existing

    def search(self, filters):
        results = list(self._sources.values())
        query = (filters.get("query") or "").strip().lower()
        if query:
            results = [item for item in results if self._matches_query(item, query)]
        source_type = filters.get("source_type")
        if source_type is not None and str(source_type).strip() != "":
            wanted = source_type.value if isinstance(source_type, SourceType) else str(source_type).strip().lower()
            results = [item for item in results if item.source_type.value == wanted]
        verification_status = filters.get("verification_status")
        if verification_status is not None and str(verification_status).strip() != "":
            wanted = verification_status.value if isinstance(verification_status, VerificationStatus) else str(verification_status).strip().lower()
            results = [item for item in results if item.verification_status.value == wanted]
        nasa_report_id = filters.get("nasa_report_id")
        if nasa_report_id is not None and str(nasa_report_id).strip() != "":
            wanted = str(nasa_report_id).strip().lower()
            results = [item for item in results if (item.nasa_report_id or "").strip().lower() == wanted]
        publisher = filters.get("publisher")
        if publisher is not None and str(publisher).strip() != "":
            wanted = str(publisher).strip().lower()
            results = [item for item in results if wanted in (item.publisher or "").lower()]
        return results

    def _matches_query(self, source: Source, query: str):
        fields = [source.id, source.title, source.nasa_report_id, source.doi, source.publisher, source.description]
        return any(query in (field or "").lower() for field in fields)
