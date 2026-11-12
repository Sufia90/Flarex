from app.repositories.experiment_repository import ExperimentNotFoundError, ExperimentRepository
from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.experiment import Experiment
from app.schemas.hardware import Hardware
from app.schemas.mission_relevance import MissionContext, MissionRelevanceAssessment, RelevanceLevel

METHODOLOGY_EXPERIMENT = (
    "Relevance is assessed only from documented fields: mission_applicability, transferability_note, findings, conditions, and source references. "
    "Documented: the mission is listed and transferability is described or findings exist. "
    "Potential: the mission is listed without a transferability description, or transferability is discussed without listing the mission. "
    "Unsupported: the mission is not listed, no transferability is described, and the experiment gravity is microgravity while the mission is Moon or Mars. "
    "Unknown: the mission is not listed and no supporting note exists. "
    "Insufficient evidence: the experiment record is too thin to assess. "
    "No numeric score is calculated. Microgravity findings never automatically transfer to partial-gravity environments."
)
METHODOLOGY_HARDWARE = (
    "Hardware mission relevance is derived from linked experiments only; it is not direct evidence about the hardware. "
    "Each linked experiment is assessed with the experiment methodology, and the strongest documented relevance is reported, "
    "with every linked experiment's level listed as supporting evidence. "
    "No numeric score is calculated. Microgravity findings never automatically transfer to partial-gravity environments."
)
LIMITATION_NO_SCORE = "No numeric relevance score is calculated; this is a qualitative assessment only."
LIMITATION_NOT_VALIDATED = "This assessment does not validate the experiment for the mission and is not an official NASA rating."
LIMITATION_MICROGRAVITY = "Microgravity findings do not automatically transfer to partial-gravity environments (Moon/Mars)."
LEVEL_ORDER = {
    RelevanceLevel.DOCUMENTED: 0,
    RelevanceLevel.POTENTIAL: 1,
    RelevanceLevel.UNKNOWN: 2,
    RelevanceLevel.INSUFFICIENT_EVIDENCE: 3,
    RelevanceLevel.UNSUPPORTED: 4,
}


class MissionRelevanceService:
    def __init__(
        self,
        experiment_repository: ExperimentRepository | None = None,
        hardware_repository: HardwareRepository | None = None,
        relationship_repository: RelationshipRepository | None = None,
    ):
        self.experiment_repository = experiment_repository or ExperimentRepository()
        self.hardware_repository = hardware_repository or HardwareRepository()
        self.relationship_repository = relationship_repository or RelationshipRepository()

    def _clean_id(self, item_id: str | None, label: str) -> str:
        cleaned = (item_id or "").strip()
        if not cleaned:
            raise ValueError(f"{label} id must not be empty")
        return cleaned

    def parse_mission(self, mission: str | None) -> MissionContext:
        cleaned = (mission or "").strip()
        for context in MissionContext:
            if context.value.lower() == cleaned.lower():
                return context
        raise ValueError("mission must be one of: ISS, Moon, Mars")

    def _enum_value(self, value):
        if value is None:
            return None
        return getattr(value, "value", value)

    def _is_microgravity(self, experiment: Experiment) -> bool:
        conditions = experiment.conditions
        if conditions is None or not conditions.gravity_condition:
            return False
        gravity = conditions.gravity_condition.lower()
        return any(word in gravity for word in ["microgravity", "micro-g", "micro g", "zero", "0g", "weightless"])

    def _has_conditions(self, experiment: Experiment) -> bool:
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

    def _relevant_conditions(self, experiment: Experiment) -> list[str]:
        conditions = experiment.conditions
        items = []
        if experiment.fuel_material:
            items.append(f"fuel material: {experiment.fuel_material}")
        if conditions is not None:
            if conditions.oxygen_concentration is not None:
                items.append(f"oxygen: {conditions.oxygen_concentration} {conditions.oxygen_unit or ''} (basis: {conditions.oxygen_basis or 'not documented'})".strip())
            if conditions.ambient_pressure is not None:
                items.append(f"pressure: {conditions.ambient_pressure} {conditions.pressure_unit or ''}".strip())
            if conditions.temperature is not None:
                items.append(f"temperature: {conditions.temperature} {conditions.temperature_unit or ''}".strip())
            if conditions.airflow_velocity is not None:
                items.append(f"airflow: {conditions.airflow_velocity} {conditions.airflow_unit or ''}".strip())
            if conditions.gravity_condition:
                items.append(f"gravity: {conditions.gravity_condition}")
        if experiment.sample_geometry:
            items.append(f"sample geometry: {experiment.sample_geometry}")
        return items

    def _assess_experiment_record(self, experiment: Experiment, mission: MissionContext) -> MissionRelevanceAssessment:
        mission_value = mission.value
        listed = mission_value in [item for item in (experiment.mission_applicability or [])]
        note = (experiment.transferability_note or "").strip()
        has_findings = bool(experiment.findings)
        has_conditions = self._has_conditions(experiment)
        has_sources = bool(experiment.source_ids)
        is_microgravity = self._is_microgravity(experiment)
        partial_mission = mission in (MissionContext.MOON, MissionContext.MARS)
        thin = not has_conditions and not has_findings and not listed and not note and not has_sources
        if thin:
            level = RelevanceLevel.INSUFFICIENT_EVIDENCE
        elif listed and (note or has_findings):
            level = RelevanceLevel.DOCUMENTED
        elif listed:
            level = RelevanceLevel.POTENTIAL
        elif note:
            level = RelevanceLevel.POTENTIAL
        elif is_microgravity and partial_mission:
            level = RelevanceLevel.UNSUPPORTED
        else:
            level = RelevanceLevel.UNKNOWN
        similarities = []
        differences = []
        if listed:
            similarities.append(f"This mission ({mission_value}) is listed in the experiment's mission applicability.")
        if mission == MissionContext.ISS and is_microgravity:
            similarities.append("Experiment was conducted in microgravity, matching the ISS environment.")
        if partial_mission and experiment.conditions and experiment.conditions.gravity_condition:
            gravity = experiment.conditions.gravity_condition.lower()
            if "lunar" in gravity or "moon" in gravity:
                similarities.append("Experiment gravity is documented as lunar gravity.")
            if "martian" in gravity or "mars" in gravity:
                similarities.append("Experiment gravity is documented as Martian gravity.")
        if is_microgravity and partial_mission:
            differences.append("Experiment gravity is microgravity; Moon/Mars gravity is partial gravity.")
        if mission == MissionContext.ISS and not is_microgravity and has_conditions:
            differences.append("Experiment gravity is not documented as microgravity, so it differs from the ISS environment.")
        supporting_evidence = []
        if listed:
            supporting_evidence.append(f"Mission {mission_value} is listed in mission_applicability.")
        if note:
            supporting_evidence.append(f"Transferability note: {note}")
        for finding in experiment.findings or []:
            supporting_evidence.append(f"Finding: {finding.title}")
        transferability_limitations = []
        if is_microgravity and partial_mission:
            transferability_limitations.append(LIMITATION_MICROGRAVITY)
        if not listed:
            transferability_limitations.append(f"This mission ({mission_value}) is not listed in the experiment's mission applicability.")
        if not note:
            transferability_limitations.append("No transferability note is documented for this experiment.")
        transferability_limitations.append("Relevance is an exploratory interpretation, not an official NASA validation.")
        missing = []
        if not has_conditions:
            missing.append("Experimental conditions are not documented.")
        if not has_findings:
            missing.append("No findings are documented.")
        if not has_sources:
            missing.append("No source references are documented.")
        if not note:
            missing.append("No transferability note is documented.")
        source_ids = sorted(set(experiment.source_ids or []) | {finding.source_id for finding in (experiment.findings or []) if finding.source_id})
        if level == RelevanceLevel.DOCUMENTED:
            explanation = f"Relevance for {mission_value} is documented: the mission is listed in mission_applicability and transferability is described or findings exist."
        elif level == RelevanceLevel.POTENTIAL:
            explanation = f"Relevance for {mission_value} is potential: the mission is listed without a transferability description, or transferability is discussed without listing this mission."
        elif level == RelevanceLevel.UNSUPPORTED:
            explanation = f"Relevance for {mission_value} is unsupported: the mission is not listed, no transferability is described, and the experiment gravity is microgravity while {mission_value} is a partial-gravity environment."
        elif level == RelevanceLevel.INSUFFICIENT_EVIDENCE:
            explanation = f"Relevance for {mission_value} cannot be assessed: the experiment record has no documented conditions, findings, mission applicability, transferability note, or source references."
        else:
            explanation = f"Relevance for {mission_value} is unknown: the mission is not listed and no supporting transferability note exists."
        limitations = [LIMITATION_NO_SCORE, LIMITATION_NOT_VALIDATED]
        if is_microgravity and partial_mission:
            limitations.append(LIMITATION_MICROGRAVITY)
        return MissionRelevanceAssessment(
            assessment_id=f"mr-exp-{experiment.id}-{mission_value}",
            subject_type="experiment",
            subject_id=experiment.id,
            subject_name=experiment.name,
            mission=mission,
            relevance_level=level,
            relevant_conditions=self._relevant_conditions(experiment),
            similarities=similarities,
            differences=differences,
            supporting_evidence=supporting_evidence,
            transferability_limitations=transferability_limitations,
            missing_information=missing,
            source_ids=source_ids,
            evidence_status=self._enum_value(experiment.data_quality.verification_status),
            derived_from_experiment_ids=[],
            explanation=explanation,
            limitations=limitations,
            methodology=METHODOLOGY_EXPERIMENT,
        )

    def assess_experiment(self, experiment_id: str, mission: str | MissionContext) -> MissionRelevanceAssessment:
        cleaned = self._clean_id(experiment_id, "experiment")
        context = mission if isinstance(mission, MissionContext) else self.parse_mission(mission)
        experiment = self.experiment_repository.get_by_id(cleaned)
        if experiment is None:
            raise ExperimentNotFoundError(cleaned)
        return self._assess_experiment_record(experiment, context)

    def assess_hardware(self, hardware_id: str, mission: str | MissionContext) -> MissionRelevanceAssessment:
        cleaned = self._clean_id(hardware_id, "hardware")
        context = mission if isinstance(mission, MissionContext) else self.parse_mission(mission)
        hardware = self.hardware_repository.get_by_id(cleaned)
        if hardware is None:
            raise HardwareNotFoundError(cleaned)
        relationships = self.relationship_repository.get_by_hardware_id(hardware.id)
        experiment_ids = sorted({relationship.experiment_id for relationship in relationships})
        experiments = []
        for experiment_id in experiment_ids:
            experiment = self.experiment_repository.get_by_id(experiment_id)
            if experiment is not None:
                experiments.append(experiment)
        if not experiments:
            return MissionRelevanceAssessment(
                assessment_id=f"mr-hw-{hardware.id}-{context.value}",
                subject_type="hardware",
                subject_id=hardware.id,
                subject_name=hardware.name,
                mission=context,
                relevance_level=RelevanceLevel.INSUFFICIENT_EVIDENCE,
                relevant_conditions=[],
                similarities=[],
                differences=[],
                supporting_evidence=[],
                transferability_limitations=["Hardware mission relevance is derived from linked experiments only; no linked experiments are documented for this hardware."],
                missing_information=["No linked experiments are documented for this hardware.", "No mission relevance evidence is available for this hardware."],
                source_ids=sorted(set(hardware.source_ids or [])),
                evidence_status=self._enum_value(hardware.data_quality.verification_status),
                derived_from_experiment_ids=[],
                explanation=f"Relevance for {context.value} cannot be assessed: no linked experiments are documented for this hardware.",
                limitations=[LIMITATION_NO_SCORE, "Hardware mission relevance is derived from linked experiments only; it is not direct evidence about the hardware."],
                methodology=METHODOLOGY_HARDWARE,
            )
        assessments = [self._assess_experiment_record(experiment, context) for experiment in experiments]
        best = min(assessments, key=lambda item: LEVEL_ORDER[item.relevance_level])
        relevant_conditions = sorted({item for assessment in assessments for item in assessment.relevant_conditions})
        similarities = sorted({item for assessment in assessments for item in assessment.similarities})
        differences = sorted({item for assessment in assessments for item in assessment.differences})
        supporting_evidence = [f"Experiment {assessment.subject_id}: {assessment.relevance_level.value}." for assessment in assessments]
        supporting_evidence.extend(sorted({item for assessment in assessments for item in assessment.supporting_evidence}))
        transferability_limitations = sorted({item for assessment in assessments for item in assessment.transferability_limitations})
        missing = sorted({item for assessment in assessments for item in assessment.missing_information})
        source_ids = sorted({source for assessment in assessments for source in assessment.source_ids} | set(hardware.source_ids or []))
        limitations = [LIMITATION_NO_SCORE, "Hardware mission relevance is derived from linked experiments only; it is not direct evidence about the hardware.", LIMITATION_NOT_VALIDATED]
        if any(assessment.relevance_level == RelevanceLevel.UNSUPPORTED for assessment in assessments):
            limitations.append(LIMITATION_MICROGRAVITY)
        return MissionRelevanceAssessment(
            assessment_id=f"mr-hw-{hardware.id}-{context.value}",
            subject_type="hardware",
            subject_id=hardware.id,
            subject_name=hardware.name,
            mission=context,
            relevance_level=best.relevance_level,
            relevant_conditions=relevant_conditions,
            similarities=similarities,
            differences=differences,
            supporting_evidence=supporting_evidence,
            transferability_limitations=transferability_limitations,
            missing_information=missing,
            source_ids=source_ids,
            evidence_status=None,
            derived_from_experiment_ids=[experiment.id for experiment in experiments],
            explanation=f"Derived from {len(experiments)} linked experiment(s). Strongest documented relevance for {context.value} is {best.relevance_level.value}. This is a derived assessment, not direct hardware evidence.",
            limitations=limitations,
            methodology=METHODOLOGY_HARDWARE,
        )
