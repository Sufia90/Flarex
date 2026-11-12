from app.repositories.experiment_repository import ExperimentNotFoundError, ExperimentRepository
from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment
from app.schemas.fire_safety import FireSafetyCategory, FireSafetyEvidenceStatus, FireSafetyInsight, FireSafetySummary

METHODOLOGY = "Insights are built from an experiment's listed fire safety categories and from categories explicitly tagged on its findings. A finding supports a category only when its fire_safety_relevance lists that category. No keyword guessing and no unit conversion are used."

LIMITATION_NOT_CERTIFICATION = "This insight organises documented research evidence; it is not a fire prediction, safety certification, or emergency guidance."
LIMITATION_POTENTIAL_NOT_PROVEN = "Potential applications are possible uses only, not proven outcomes."
LIMITATION_NO_SOURCES = "No source references are documented for this insight."
LIMITATION_DERIVED = "Derived from linked experiment records; hardware was not directly assessed."

POTENTIAL_APPLICATIONS = {
    "prevention": "Potential application: informing choices about materials and oxygen conditions to reduce combustion likelihood in spacecraft and habitats; requires further validation.",
    "detection": "Potential application: informing approaches to smoke and combustion-product monitoring; requires further validation.",
    "suppression": "Potential application: informing research into flame suppression methods; requires further validation.",
}


class FireSafetyService:
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

    def _coerce_category(self, category):
        if isinstance(category, FireSafetyCategory):
            return category
        return FireSafetyCategory(category)

    def _tagged_findings(self, experiment: Experiment, category: FireSafetyCategory):
        return [finding for finding in (experiment.findings or []) if category.value in (finding.fire_safety_relevance or [])]

    def _relevant_categories(self, experiment: Experiment) -> list[FireSafetyCategory]:
        categories = []
        for category_value in (experiment.fire_safety_relevance or []):
            category = self._coerce_category(category_value)
            if category not in categories:
                categories.append(category)
        for category in FireSafetyCategory:
            if category not in categories and self._tagged_findings(experiment, category):
                categories.append(category)
        return categories

    def _collect_source_ids(self, experiment: Experiment, findings):
        source_ids = set(experiment.source_ids or [])
        for finding in findings:
            if finding.source_id:
                source_ids.add(finding.source_id)
        return sorted(source_ids)

    def _build_insight(self, experiment: Experiment, category: FireSafetyCategory) -> FireSafetyInsight:
        tagged = self._tagged_findings(experiment, category)
        source_ids = self._collect_source_ids(experiment, tagged)
        documented_evidence = []
        for finding in tagged:
            if finding.observation:
                documented_evidence.append(f"Finding {finding.title}: {finding.observation}")
            if finding.conclusion:
                documented_evidence.append(f"Finding {finding.title}: {finding.conclusion}")
            if not finding.observation and not finding.conclusion:
                documented_evidence.append(f"Finding {finding.title}: documented finding.")
        if tagged and source_ids:
            status = FireSafetyEvidenceStatus.DOCUMENTED
            explanation = f"Documented {category.value} evidence: {len(tagged)} tagged finding(s) with source references."
        elif tagged:
            status = FireSafetyEvidenceStatus.POTENTIAL
            explanation = f"Potential {category.value} evidence: {len(tagged)} tagged finding(s) but no source references documented."
        elif experiment.findings:
            status = FireSafetyEvidenceStatus.POTENTIAL
            explanation = f"Potential {category.value} evidence: category listed for this experiment, but no findings are tagged for it yet."
        else:
            status = FireSafetyEvidenceStatus.INSUFFICIENT_EVIDENCE
            explanation = f"Insufficient evidence: category listed for this experiment, but no findings are documented."
        derived_interpretation = []
        if tagged:
            derived_interpretation.append(f"Interpretation: {len(tagged)} tagged finding(s) describe {category.value} evidence for this experiment. This is an interpretation of documented evidence, not a new finding.")
        potential_applications = []
        if status in (FireSafetyEvidenceStatus.DOCUMENTED, FireSafetyEvidenceStatus.POTENTIAL):
            potential_applications.append(POTENTIAL_APPLICATIONS[category.value])
        limitations = [LIMITATION_NOT_CERTIFICATION]
        if potential_applications:
            limitations.append(LIMITATION_POTENTIAL_NOT_PROVEN)
        if not source_ids:
            limitations.append(LIMITATION_NO_SOURCES)
        missing_information = []
        if not tagged:
            missing_information.append("No findings tagged for this category.")
        if not source_ids:
            missing_information.append("No source references documented.")
        return FireSafetyInsight(
            insight_id=f"fs-{experiment.id}-{category.value}",
            category=category,
            evidence_status=status,
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            hardware_ids=list(experiment.hardware_ids or []),
            finding_ids=[finding.id for finding in tagged],
            source_ids=source_ids,
            documented_evidence=documented_evidence,
            derived_interpretation=derived_interpretation,
            potential_applications=potential_applications,
            limitations=limitations,
            missing_information=missing_information,
            verification_status=self._enum_value(experiment.data_quality.verification_status),
            derived=False,
            methodology=METHODOLOGY,
            explanation=explanation,
        )

    def _build_unlisted_insight(self, experiment: Experiment, category: FireSafetyCategory) -> FireSafetyInsight:
        if experiment.findings:
            status = FireSafetyEvidenceStatus.UNSUPPORTED
            explanation = f"Unsupported {category.value} evidence: category is not listed as relevant for this experiment and no findings are tagged for it."
        else:
            status = FireSafetyEvidenceStatus.UNKNOWN
            explanation = f"Unknown {category.value} evidence: category is not listed for this experiment and no findings are documented."
        return FireSafetyInsight(
            insight_id=f"fs-{experiment.id}-{category.value}",
            category=category,
            evidence_status=status,
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            hardware_ids=list(experiment.hardware_ids or []),
            finding_ids=[],
            source_ids=sorted(set(experiment.source_ids or [])),
            documented_evidence=[],
            derived_interpretation=[],
            potential_applications=[],
            limitations=[LIMITATION_NOT_CERTIFICATION, "This category is not listed as relevant for this experiment."],
            missing_information=["No findings tagged for this category.", "Category relevance not documented for this experiment."],
            verification_status=self._enum_value(experiment.data_quality.verification_status),
            derived=False,
            methodology=METHODOLOGY,
            explanation=explanation,
        )

    def get_all_insights(self) -> list[FireSafetyInsight]:
        insights = []
        for experiment in self.experiment_repository.get_all():
            for category in self._relevant_categories(experiment):
                insights.append(self._build_insight(experiment, category))
        return insights

    def get_insights_by_category(self, category) -> list[FireSafetyInsight]:
        category = self._coerce_category(category)
        return [insight for insight in self.get_all_insights() if insight.category == category]

    def get_insights_for_experiment(self, experiment_id: str) -> list[FireSafetyInsight]:
        experiment = self.experiment_repository.get_by_id(experiment_id)
        if experiment is None:
            raise ExperimentNotFoundError(experiment_id)
        return [self._build_insight(experiment, category) for category in self._relevant_categories(experiment)]

    def get_insight_for_experiment_category(self, experiment_id: str, category) -> FireSafetyInsight:
        category = self._coerce_category(category)
        experiment = self.experiment_repository.get_by_id(experiment_id)
        if experiment is None:
            raise ExperimentNotFoundError(experiment_id)
        if category.value in (experiment.fire_safety_relevance or []) or self._tagged_findings(experiment, category):
            return self._build_insight(experiment, category)
        return self._build_unlisted_insight(experiment, category)

    def get_insights_for_hardware(self, hardware_id: str) -> list[FireSafetyInsight]:
        hardware = self.hardware_repository.get_by_id(hardware_id)
        if hardware is None:
            raise HardwareNotFoundError(hardware_id)
        relationships = self.relationship_repository.get_by_hardware_id(hardware.id)
        experiment_ids = sorted({relationship.experiment_id for relationship in relationships})
        insights = []
        for experiment_id in experiment_ids:
            experiment = self.experiment_repository.get_by_id(experiment_id)
            if experiment is None:
                continue
            for category in self._relevant_categories(experiment):
                insight = self._build_insight(experiment, category)
                derived = insight.model_copy(update={
                    "insight_id": f"fs-hw-{hardware.id}-{experiment.id}-{category.value}",
                    "derived": True,
                    "hardware_ids": [hardware.id],
                    "explanation": insight.explanation + f" Derived from linked experiment {experiment.id}.",
                    "limitations": insight.limitations + [LIMITATION_DERIVED],
                })
                insights.append(derived)
        return insights

    def search_insights(self, category=None, experiment_id: str | None = None, hardware_id: str | None = None, evidence_status=None, mission: str | None = None) -> list[FireSafetyInsight]:
        if experiment_id is not None and self.experiment_repository.get_by_id(experiment_id) is None:
            raise ExperimentNotFoundError(experiment_id)
        if hardware_id is not None and self.hardware_repository.get_by_id(hardware_id) is None:
            raise HardwareNotFoundError(hardware_id)
        if mission is not None:
            allowed = {"iss", "moon", "mars"}
            if mission.strip().lower() not in allowed:
                raise ValueError("mission must be one of: ISS, Moon, Mars")
        insights = self.get_all_insights()
        if category is not None:
            category = self._coerce_category(category)
            insights = [insight for insight in insights if insight.category == category]
        if experiment_id is not None:
            insights = [insight for insight in insights if insight.experiment_id == experiment_id]
        if hardware_id is not None:
            insights = [insight for insight in insights if hardware_id in (insight.hardware_ids or [])]
        if evidence_status is not None:
            if isinstance(evidence_status, str):
                evidence_status = FireSafetyEvidenceStatus(evidence_status)
            insights = [insight for insight in insights if insight.evidence_status == evidence_status]
        if mission is not None:
            mission_experiments = {experiment.id for experiment in self.experiment_repository.get_all() if mission.strip().lower() in [value.lower() for value in (experiment.mission_applicability or [])]}
            insights = [insight for insight in insights if insight.experiment_id in mission_experiments]
        return insights

    def get_summary(self) -> FireSafetySummary:
        experiments = self.experiment_repository.get_all()
        insights = self.get_all_insights()
        counts = {status: 0 for status in FireSafetyEvidenceStatus}
        for insight in insights:
            counts[insight.evidence_status] += 1
        with_evidence = len({insight.experiment_id for insight in insights if insight.experiment_id})
        return FireSafetySummary(
            total_experiments=len(experiments),
            total_insights=len(insights),
            prevention_count=len([insight for insight in insights if insight.category == FireSafetyCategory.PREVENTION]),
            detection_count=len([insight for insight in insights if insight.category == FireSafetyCategory.DETECTION]),
            suppression_count=len([insight for insight in insights if insight.category == FireSafetyCategory.SUPPRESSION]),
            documented_count=counts[FireSafetyEvidenceStatus.DOCUMENTED],
            potential_count=counts[FireSafetyEvidenceStatus.POTENTIAL],
            unsupported_count=counts[FireSafetyEvidenceStatus.UNSUPPORTED],
            unknown_count=counts[FireSafetyEvidenceStatus.UNKNOWN],
            insufficient_evidence_count=counts[FireSafetyEvidenceStatus.INSUFFICIENT_EVIDENCE],
            experiments_with_evidence=with_evidence,
            experiments_without_evidence=len(experiments) - with_evidence,
            limitations=["Counts reflect documented evidence only.", "An empty dataset produces zero counts."],
            explanation="Summary counts insights derived from documented experiment records. Zero counts mean no evidence is documented, not that the category is impossible.",
        )
