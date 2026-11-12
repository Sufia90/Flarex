from app.repositories.experiment_repository import ExperimentNotFoundError, ExperimentRepository
from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment
from app.schemas.hardware import Hardware
from app.schemas.ranking import RankingCriterion, RankingItem, RankingRequest, RankingResult, RankingStatus

DOCUMENTATION_SIGNALS = [
    "name",
    "description",
    "scientific_objective",
    "research_category",
    "conditions",
    "measurements",
    "findings",
    "source_references",
    "limitations",
]


class RankingService:
    def __init__(
        self,
        experiment_repository: ExperimentRepository | None = None,
        hardware_repository: HardwareRepository | None = None,
        relationship_repository: RelationshipRepository | None = None,
    ):
        self.experiment_repository = experiment_repository or ExperimentRepository()
        self.hardware_repository = hardware_repository or HardwareRepository()
        self.relationship_repository = relationship_repository or RelationshipRepository()

    def _enum_value(self, value):
        if value is None:
            return None
        return getattr(value, "value", value)

    def _resolve_hardware(self, item_ids: list[str] | None) -> list[Hardware]:
        if item_ids is None:
            return self.hardware_repository.get_all()
        if not item_ids:
            raise ValueError("item_ids must not be empty when provided")
        cleaned = [(item_id or "").strip() for item_id in item_ids]
        if any(not item_id for item_id in cleaned):
            raise ValueError("item_ids must not be empty")
        if len({item_id.lower() for item_id in cleaned}) != len(cleaned):
            raise ValueError("Duplicate item ids are not allowed")
        found = []
        for item_id in cleaned:
            hardware = self.hardware_repository.get_by_id(item_id)
            if hardware is None:
                raise HardwareNotFoundError(item_id)
            found.append(hardware)
        return found

    def _resolve_experiments(self, item_ids: list[str] | None) -> list[Experiment]:
        if item_ids is None:
            return self.experiment_repository.get_all()
        if not item_ids:
            raise ValueError("item_ids must not be empty when provided")
        cleaned = [(item_id or "").strip() for item_id in item_ids]
        if any(not item_id for item_id in cleaned):
            raise ValueError("item_ids must not be empty")
        if len({item_id.lower() for item_id in cleaned}) != len(cleaned):
            raise ValueError("Duplicate item ids are not allowed")
        found = []
        for item_id in cleaned:
            experiment = self.experiment_repository.get_by_id(item_id)
            if experiment is None:
                raise ExperimentNotFoundError(item_id)
            found.append(experiment)
        return found

    def _assign_ranks(self, items: list[RankingItem]) -> list[RankingItem]:
        ordered = sorted(items, key=lambda item: (-item.metric_value, item.item_id))
        rank = 0
        previous_value = None
        for item in ordered:
            if item.metric_value <= 0:
                item.rank = None
                continue
            if previous_value is None or item.metric_value != previous_value:
                rank += 1
                previous_value = item.metric_value
            item.rank = rank
        return ordered

    def _build_result(self, request: RankingRequest, title: str, question: str, methodology: str, metric_name: str, metric_description: str, metric_max: int | None, items: list[RankingItem], source_ids: list[str], limitations: list[str]) -> RankingResult:
        ranked = [item for item in items if item.rank is not None]
        if len(ranked) < 2:
            status = RankingStatus.INSUFFICIENT_EVIDENCE
            explanation = "Insufficient evidence: fewer than two items have evidence for this criterion, so no meaningful ranking can be produced. Items are listed without ranks."
        else:
            status = RankingStatus.RANKED
            explanation = f"Ranked {len(ranked)} items by {metric_name}. Items without evidence are listed without a rank and are not treated as lowest-performing."
        if status == RankingStatus.INSUFFICIENT_EVIDENCE:
            for item in items:
                item.rank = None
        total = len(items)
        shown = items[: request.limit]
        if total > request.limit:
            limitations = limitations + [f"Result limited to the first {request.limit} items of {total} eligible items."]
        return RankingResult(
            ranking_id="rank-" + request.criterion.value,
            criterion=request.criterion,
            title=title,
            question=question,
            methodology=methodology,
            metric_name=metric_name,
            metric_description=metric_description,
            metric_max=metric_max,
            status=status,
            eligible_item_ids=[item.item_id for item in items],
            items=shown,
            source_ids=sorted(set(source_ids)),
            explanation=explanation,
            limitations=limitations,
        )

    def _rank_hardware_associations(self, request: RankingRequest) -> RankingResult:
        hardware_items = self._resolve_hardware(request.item_ids)
        items = []
        source_ids = []
        for hardware in hardware_items:
            relationships = self.relationship_repository.get_by_hardware_id(hardware.id)
            distinct_experiments = sorted({relationship.experiment_id for relationship in relationships})
            evidence = sorted({relationship.id for relationship in relationships})
            source_ids.extend(evidence)
            count = len(distinct_experiments)
            if count > 0:
                explanation = f"Documented in {count} distinct experiment association(s) via {len(relationships)} relationship record(s)."
                item_limitations: list[str] = []
            else:
                explanation = "No documented experiment associations. This is missing evidence, not poor performance."
                item_limitations = ["No documented experiment associations; not ranked."]
            items.append(RankingItem(
                item_id=hardware.id,
                item_name=hardware.name,
                metric_value=count,
                metric_breakdown={"distinct_experiments": count, "relationships": len(relationships)},
                evidence_ids=evidence,
                data_completeness=self._enum_value(hardware.data_quality.completeness),
                verification_status=self._enum_value(hardware.data_quality.verification_status),
                explanation=explanation,
                limitations=item_limitations,
            ))
        ordered = self._assign_ranks(items)
        return self._build_result(
            request,
            title="Hardware by documented experiment associations",
            question="Which hardware has the most documented experiment associations?",
            methodology="For each hardware item, count distinct experiment ids in its documented relationships. Sort by count descending, then by hardware id ascending. Equal counts share the same rank. Items with no documented associations are listed without a rank. No weights are used and no performance claim is made.",
            metric_name="distinct_experiment_associations",
            metric_description="Number of distinct experiments linked to this hardware by documented relationships. This counts documentation, not hardware performance or safety.",
            metric_max=None,
            items=ordered,
            source_ids=source_ids,
            limitations=[
                "Association count measures documentation, not hardware performance, safety, or effectiveness.",
                "Missing relationships mean missing evidence, not poor hardware.",
                "A hardware item with no documented associations is not ranked as worst.",
            ],
        )

    def _conditions_documented(self, experiment: Experiment) -> bool:
        conditions = experiment.conditions
        if conditions is None:
            return False
        fields = [
            conditions.fuel_material,
            conditions.oxygen_concentration,
            conditions.ambient_pressure,
            conditions.temperature,
            conditions.airflow_velocity,
            conditions.gravity_condition,
            conditions.sample_geometry,
        ]
        return any(value is not None and (not isinstance(value, str) or value.strip()) for value in fields)

    def _rank_documentation_completeness(self, request: RankingRequest) -> RankingResult:
        experiments = self._resolve_experiments(request.item_ids)
        items = []
        source_ids = []
        for experiment in experiments:
            signals = {
                "name": 1 if experiment.name else 0,
                "description": 1 if experiment.description else 0,
                "scientific_objective": 1 if experiment.scientific_objective else 0,
                "research_category": 1 if experiment.research_category else 0,
                "conditions": 1 if self._conditions_documented(experiment) else 0,
                "measurements": 1 if experiment.measurements else 0,
                "findings": 1 if experiment.findings else 0,
                "source_references": 1 if experiment.source_ids else 0,
                "limitations": 1 if experiment.limitations else 0,
            }
            count = sum(signals.values())
            source_ids.extend(experiment.source_ids or [])
            missing = [name for name in DOCUMENTATION_SIGNALS if signals[name] == 0]
            if count > 0:
                explanation = f"{count} of {len(DOCUMENTATION_SIGNALS)} documentation signals present."
                item_limitations = [f"Missing documentation signals: {', '.join(missing)}."] if missing else []
            else:
                explanation = "No documentation signals present."
                item_limitations = ["No documentation signals present; not ranked."]
            items.append(RankingItem(
                item_id=experiment.id,
                item_name=experiment.name,
                metric_value=count,
                metric_max=len(DOCUMENTATION_SIGNALS),
                metric_breakdown=signals,
                evidence_ids=sorted(set(experiment.source_ids or [])),
                data_completeness=self._enum_value(experiment.data_quality.completeness),
                verification_status=self._enum_value(experiment.data_quality.verification_status),
                explanation=explanation,
                limitations=item_limitations,
            ))
        ordered = self._assign_ranks(items)
        return self._build_result(
            request,
            title="Experiments by documentation completeness",
            question="Which experiments have the most complete documentation?",
            methodology=f"For each experiment, count how many of the {len(DOCUMENTATION_SIGNALS)} documentation signals are present: {', '.join(DOCUMENTATION_SIGNALS)}. Sort by count descending, then by experiment id ascending. Equal counts share the same rank. No weights are used.",
            metric_name="documentation_signals_present",
            metric_description="Number of documentation signals present. This counts documentation completeness, not scientific effectiveness.",
            metric_max=len(DOCUMENTATION_SIGNALS),
            items=ordered,
            source_ids=source_ids,
            limitations=[
                "Documentation completeness is not scientific effectiveness.",
                "A missing signal means missing documentation, not a negative finding.",
                "An experiment with more documentation is not automatically more important.",
            ],
        )

    def _rank_measurement_coverage(self, request: RankingRequest) -> RankingResult:
        experiments = self._resolve_experiments(request.item_ids)
        items = []
        source_ids = []
        for experiment in experiments:
            measurements = experiment.measurements or []
            kinds = {"measured": 0, "derived": 0, "interpreted": 0, "unknown": 0}
            for measurement in measurements:
                kind = self._enum_value(measurement.measurement_kind) or "unknown"
                if kind not in kinds:
                    kind = "unknown"
                kinds[kind] += 1
            distinct_parameters = len({(m.parameter_name or "").strip().lower() for m in measurements if m.parameter_name})
            breakdown = dict(kinds)
            breakdown["distinct_parameters"] = distinct_parameters
            source_ids.extend([m.source_id for m in measurements if m.source_id])
            source_ids.extend(experiment.source_ids or [])
            count = len(measurements)
            if count > 0:
                explanation = f"{count} documented measurement(s) across {distinct_parameters} distinct parameter(s): measured {kinds['measured']}, derived {kinds['derived']}, interpreted {kinds['interpreted']}, unknown kind {kinds['unknown']}."
                item_limitations = []
            else:
                explanation = "No documented measurements. This is missing evidence, not poor performance."
                item_limitations = ["No documented measurements; not ranked."]
            items.append(RankingItem(
                item_id=experiment.id,
                item_name=experiment.name,
                metric_value=count,
                metric_breakdown=breakdown,
                evidence_ids=sorted({m.source_id for m in measurements if m.source_id} | set(experiment.source_ids or [])),
                data_completeness=self._enum_value(experiment.data_quality.completeness),
                verification_status=self._enum_value(experiment.data_quality.verification_status),
                explanation=explanation,
                limitations=item_limitations,
            ))
        ordered = self._assign_ranks(items)
        return self._build_result(
            request,
            title="Experiments by documented measurement coverage",
            question="Which experiments have the greatest documented measurement coverage?",
            methodology="For each experiment, count documented measurements and group them by measurement kind (measured, derived, interpreted, unknown). Sort by count descending, then by experiment id ascending. Equal counts share the same rank. Items with no documented measurements are listed without a rank. No weights are used.",
            metric_name="documented_measurements",
            metric_description="Number of documented measurements. This counts measurement coverage, not measurement quality or scientific importance.",
            metric_max=None,
            items=ordered,
            source_ids=source_ids,
            limitations=[
                "Measurement coverage is not measurement quality or scientific importance.",
                "Derived and interpreted values are counted separately from measured values and are not treated as equivalent evidence.",
                "An experiment with no documented measurements is not ranked as worst.",
            ],
        )

    def rank(self, request: RankingRequest) -> RankingResult:
        if request.criterion == RankingCriterion.HARDWARE_EXPERIMENT_ASSOCIATIONS:
            return self._rank_hardware_associations(request)
        if request.criterion == RankingCriterion.EXPERIMENT_DOCUMENTATION_COMPLETENESS:
            return self._rank_documentation_completeness(request)
        if request.criterion == RankingCriterion.EXPERIMENT_MEASUREMENT_COVERAGE:
            return self._rank_measurement_coverage(request)
        raise ValueError(f"Unsupported ranking criterion: {request.criterion}")
