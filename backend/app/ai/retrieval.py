from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.hardware_repository import HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.retrieval import RecordType, RetrievalRequest, RetrievalResponse, RetrievalResult
from app.services.fire_safety_service import FireSafetyService
from app.services.mission_relevance_service import MissionRelevanceService

METHODOLOGY = "Deterministic case-insensitive substring matching over structured record fields. This is keyword retrieval, not semantic AI retrieval."
MISSIONS = ("ISS", "Moon", "Mars")


class RetrievalService:
    def __init__(
        self,
        experiment_repository: ExperimentRepository | None = None,
        hardware_repository: HardwareRepository | None = None,
        relationship_repository: RelationshipRepository | None = None,
        source_repository: SourceRepository | None = None,
        fire_safety_service: FireSafetyService | None = None,
        mission_relevance_service: MissionRelevanceService | None = None,
    ):
        self.experiment_repository = experiment_repository or ExperimentRepository()
        self.hardware_repository = hardware_repository or HardwareRepository()
        self.relationship_repository = relationship_repository or RelationshipRepository()
        self.source_repository = source_repository or SourceRepository()
        self.fire_safety_service = fire_safety_service or FireSafetyService(
            experiment_repository=self.experiment_repository,
            hardware_repository=self.hardware_repository,
            relationship_repository=self.relationship_repository,
        )
        self.mission_relevance_service = mission_relevance_service or MissionRelevanceService(
            experiment_repository=self.experiment_repository,
            hardware_repository=self.hardware_repository,
            relationship_repository=self.relationship_repository,
        )

    def _enum_value(self, value):
        if value is None:
            return None
        return getattr(value, "value", value)

    def _matched_fields(self, fields, query: str) -> list[str]:
        lowered = query.lower()
        return [name for name, value in fields if value and lowered in value.lower()]

    def _search_experiments(self, query: str) -> list[RetrievalResult]:
        results = []
        for experiment in self.experiment_repository.get_all():
            fields = [
                ("name", experiment.name),
                ("acronym", experiment.acronym),
                ("description", experiment.description),
                ("scientific_objective", experiment.scientific_objective),
                ("research_category", experiment.research_category),
                ("combustion_type", experiment.combustion_type),
                ("fuel_material", experiment.fuel_material),
                ("nasa_investigation_id", experiment.nasa_investigation_id),
            ]
            matched = self._matched_fields(fields, query)
            if not matched:
                continue
            results.append(RetrievalResult(
                record_type=RecordType.EXPERIMENT,
                record_id=experiment.id,
                title=experiment.name,
                text=" ".join(value for _, value in fields if value),
                experiment_id=experiment.id,
                source_ids=sorted(set(experiment.source_ids or [])),
                verification_status=self._enum_value(experiment.data_quality.verification_status),
                evidence_category=experiment.research_category,
                limitations=list(experiment.limitations or []),
                matched_fields=matched,
            ))
        return results

    def _search_findings(self, query: str) -> list[RetrievalResult]:
        results = []
        for experiment in self.experiment_repository.get_all():
            for finding in (experiment.findings or []):
                fields = [
                    ("title", finding.title),
                    ("observation", finding.observation),
                    ("conclusion", finding.conclusion),
                ]
                matched = self._matched_fields(fields, query)
                if not matched:
                    continue
                results.append(RetrievalResult(
                    record_type=RecordType.FINDING,
                    record_id=finding.id,
                    title=finding.title,
                    text=" ".join(value for _, value in fields if value),
                    experiment_id=experiment.id,
                    source_ids=[finding.source_id] if finding.source_id else [],
                    verification_status=self._enum_value(finding.verification_status),
                    evidence_category=", ".join(finding.fire_safety_relevance or []) or None,
                    limitations=list(finding.limitations or []),
                    matched_fields=matched,
                ))
        return results

    def _search_measurements(self, query: str) -> list[RetrievalResult]:
        results = []
        for experiment in self.experiment_repository.get_all():
            for measurement in (experiment.measurements or []):
                fields = [
                    ("parameter_name", measurement.parameter_name),
                    ("parameter_description", measurement.parameter_description),
                    ("value", str(measurement.value) if measurement.value is not None else None),
                    ("unit", measurement.unit),
                    ("measurement_method", measurement.measurement_method),
                    ("sensor", measurement.sensor),
                ]
                matched = self._matched_fields(fields, query)
                if not matched:
                    continue
                results.append(RetrievalResult(
                    record_type=RecordType.MEASUREMENT,
                    record_id=measurement.id,
                    title=measurement.parameter_name,
                    text=" ".join(value for _, value in fields if value),
                    experiment_id=experiment.id,
                    source_ids=[measurement.source_id] if measurement.source_id else [],
                    verification_status=self._enum_value(measurement.verification_status),
                    evidence_category=self._enum_value(measurement.measurement_kind),
                    limitations=[],
                    matched_fields=matched,
                ))
        return results

    def _search_hardware(self, query: str) -> list[RetrievalResult]:
        results = []
        for hardware in self.hardware_repository.get_all():
            fields = [
                ("name", hardware.name),
                ("acronym", hardware.acronym),
                ("description", hardware.description),
                ("purpose", hardware.purpose),
                ("facility_classification", hardware.facility_classification),
            ]
            matched = self._matched_fields(fields, query)
            if not matched:
                continue
            results.append(RetrievalResult(
                record_type=RecordType.HARDWARE,
                record_id=hardware.id,
                title=hardware.name,
                text=" ".join(value for _, value in fields if value),
                hardware_id=hardware.id,
                source_ids=sorted(set(hardware.source_ids or [])),
                verification_status=self._enum_value(hardware.data_quality.verification_status),
                evidence_category=self._enum_value(hardware.hardware_type),
                limitations=[hardware.limitations] if hardware.limitations else [],
                matched_fields=matched,
            ))
        return results

    def _search_relationships(self, query: str) -> list[RetrievalResult]:
        results = []
        for relationship in self.relationship_repository.get_all():
            fields = [
                ("role", relationship.role),
                ("evidence", relationship.evidence),
                ("notes", relationship.notes),
            ]
            matched = self._matched_fields(fields, query)
            if not matched:
                continue
            results.append(RetrievalResult(
                record_type=RecordType.RELATIONSHIP,
                record_id=relationship.id,
                title=f"{relationship.experiment_id} - {relationship.hardware_id}",
                text=" ".join(value for _, value in fields if value),
                experiment_id=relationship.experiment_id,
                hardware_id=relationship.hardware_id,
                source_ids=[relationship.source_id] if relationship.source_id else [],
                verification_status=self._enum_value(relationship.verification_status),
                evidence_category=self._enum_value(relationship.relationship_type),
                limitations=[],
                matched_fields=matched,
            ))
        return results

    def _search_sources(self, query: str) -> list[RetrievalResult]:
        results = []
        for source in self.source_repository.get_all():
            fields = [
                ("title", source.title),
                ("nasa_report_id", source.nasa_report_id),
                ("doi", source.doi),
                ("publisher", source.publisher),
                ("description", source.description),
                ("source_type", self._enum_value(source.source_type)),
            ]
            matched = self._matched_fields(fields, query)
            if not matched:
                continue
            results.append(RetrievalResult(
                record_type=RecordType.SOURCE,
                record_id=source.id,
                title=source.title,
                text=" ".join(value for _, value in fields if value),
                source_ids=[source.id],
                verification_status=self._enum_value(source.verification_status),
                evidence_category=self._enum_value(source.source_type),
                limitations=[],
                matched_fields=matched,
            ))
        return results

    def _search_fire_safety_insights(self, query: str) -> list[RetrievalResult]:
        results = []
        for insight in self.fire_safety_service.get_all_insights():
            fields = [
                ("category", insight.category.value),
                ("explanation", insight.explanation),
                ("documented_evidence", " ".join(insight.documented_evidence)),
                ("experiment_name", insight.experiment_name),
            ]
            matched = self._matched_fields(fields, query)
            if not matched:
                continue
            results.append(RetrievalResult(
                record_type=RecordType.FIRE_SAFETY_INSIGHT,
                record_id=insight.insight_id,
                title=f"{insight.experiment_name} - {insight.category.value} fire safety insight",
                text=" ".join(value for _, value in fields if value),
                experiment_id=insight.experiment_id,
                source_ids=list(insight.source_ids or []),
                verification_status=insight.verification_status,
                evidence_category=insight.category.value,
                limitations=list(insight.limitations or []),
                matched_fields=matched,
            ))
        return results

    def _search_mission_relevance(self, query: str) -> list[RetrievalResult]:
        results = []
        for experiment in self.experiment_repository.get_all():
            for mission in MISSIONS:
                assessment = self.mission_relevance_service.assess_experiment(experiment.id, mission)
                text = " ".join([assessment.explanation] + list(assessment.similarities or []) + list(assessment.differences or []))
                fields = [
                    ("mission", mission),
                    ("relevance_level", assessment.relevance_level.value),
                    ("explanation", text),
                ]
                matched = self._matched_fields(fields, query)
                if not matched:
                    continue
                results.append(RetrievalResult(
                    record_type=RecordType.MISSION_RELEVANCE,
                    record_id=assessment.assessment_id,
                    title=f"{experiment.name} - {mission} relevance",
                    text=text,
                    experiment_id=experiment.id,
                    source_ids=list(assessment.source_ids or []),
                    verification_status=self._enum_value(assessment.evidence_status),
                    evidence_category=mission,
                    limitations=list(assessment.limitations or []),
                    matched_fields=matched,
                ))
        return results

    def search(self, request: RetrievalRequest) -> RetrievalResponse:
        query = (request.query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        wanted = request.record_types or list(RecordType)
        results = []
        if RecordType.EXPERIMENT in wanted:
            results.extend(self._search_experiments(query))
        if RecordType.FINDING in wanted:
            results.extend(self._search_findings(query))
        if RecordType.MEASUREMENT in wanted:
            results.extend(self._search_measurements(query))
        if RecordType.HARDWARE in wanted:
            results.extend(self._search_hardware(query))
        if RecordType.RELATIONSHIP in wanted:
            results.extend(self._search_relationships(query))
        if RecordType.SOURCE in wanted:
            results.extend(self._search_sources(query))
        if RecordType.FIRE_SAFETY_INSIGHT in wanted:
            results.extend(self._search_fire_safety_insights(query))
        if RecordType.MISSION_RELEVANCE in wanted:
            results.extend(self._search_mission_relevance(query))
        if request.experiment_id is not None:
            results = [result for result in results if result.experiment_id == request.experiment_id]
        total = len(results)
        shown = results[: request.limit]
        if total == 0:
            explanation = "No relevant records found for this query."
        else:
            explanation = f"{total} relevant record(s) found by deterministic text matching."
        limitations = [
            "Keyword matching only; synonyms and related concepts are not found.",
            "Results are ordered by record type, not by relevance score.",
        ]
        return RetrievalResponse(
            query=request.query,
            total=total,
            results=shown,
            methodology=METHODOLOGY,
            explanation=explanation,
            limitations=limitations,
        )
