from app.repositories.experiment_repository import ExperimentNotFoundError, ExperimentRepository
from app.repositories.hardware_repository import HardwareNotFoundError, HardwareRepository
from app.schemas.comparison import (
    ComparabilityStatus,
    ComparisonCategory,
    ComparedValue,
    ConditionComparison,
    ExperimentComparison,
    HardwareComparison,
    MeasurementComparison,
    ParameterComparison,
)
from app.schemas.experiment import Experiment, Measurement
from app.schemas.hardware import Hardware

METHODOLOGY_EXPERIMENTS = (
    "Parameters are matched by parameter name. A parameter is comparable only when all documented values use the same unit, "
    "the same measurement kind and method, and the compared experiments share the same documented fuel, gravity, oxygen, "
    "pressure, temperature, airflow and sample conditions. Units are never converted and missing values are never treated as zero."
)
METHODOLOGY_HARDWARE = (
    "Hardware fields are compared by field name. Shared and unique supported measurements are listed separately. "
    "Different hardware types serve different purposes and are not directly interchangeable. "
    "This comparison does not rank hardware by performance, safety, or effectiveness."
)
METHODOLOGY_MEASUREMENTS = (
    "Measurements are matched by parameter name across their parent experiments. A parameter is comparable only when all "
    "documented values use the same unit, the same measurement kind and method, and the parent experiments share the same "
    "documented conditions. Units are never converted and missing values are never treated as zero."
)
LIMITATION_NO_CAUSATION = "This comparison describes documented differences only; it does not claim causation."
LIMITATION_NO_CONVERSION = "Units were not converted; values with different units were not directly compared."
LIMITATION_MISSING_NOT_ZERO = "Missing values are not treated as zero."


class MeasurementNotFoundError(KeyError):
    pass


class ComparisonService:
    def __init__(
        self,
        experiment_repository: ExperimentRepository | None = None,
        hardware_repository: HardwareRepository | None = None,
    ):
        self.experiment_repository = experiment_repository or ExperimentRepository()
        self.hardware_repository = hardware_repository or HardwareRepository()

    def _clean_ids(self, ids: list[str] | None, label: str) -> list[str]:
        if ids is None or len(ids) < 2:
            raise ValueError(f"At least two {label} ids are required")
        if len(ids) > 10:
            raise ValueError(f"At most ten {label} ids are allowed")
        cleaned = [(item_id or "").strip() for item_id in ids]
        if any(not item_id for item_id in cleaned):
            raise ValueError(f"{label} ids must not be empty")
        lowered = [item_id.lower() for item_id in cleaned]
        if len(set(lowered)) != len(lowered):
            raise ValueError(f"Duplicate {label} ids are not allowed")
        return cleaned

    def _resolve_experiments(self, ids: list[str]) -> list[Experiment]:
        found = []
        for item_id in ids:
            experiment = self.experiment_repository.get_by_id(item_id)
            if experiment is None:
                raise ExperimentNotFoundError(item_id)
            found.append(experiment)
        return found

    def _resolve_hardware(self, ids: list[str]) -> list[Hardware]:
        found = []
        for item_id in ids:
            hardware = self.hardware_repository.get_by_id(item_id)
            if hardware is None:
                raise HardwareNotFoundError(item_id)
            found.append(hardware)
        return found

    def _find_measurement(self, measurement_id: str) -> tuple[Measurement, Experiment]:
        wanted = (measurement_id or "").strip().lower()
        for experiment in self.experiment_repository.get_all():
            for measurement in experiment.measurements or []:
                if (measurement.id or "").strip().lower() == wanted:
                    return measurement, experiment
        raise MeasurementNotFoundError(measurement_id)

    def _enum_value(self, value):
        if value is None:
            return None
        return getattr(value, "value", value)

    def _format(self, value, unit: str | None) -> str:
        if value is None:
            return "missing"
        text = str(value)
        return f"{text} {unit}" if unit else text

    def _condition_keys(self, experiment: Experiment) -> dict[str, str | None]:
        conditions = experiment.conditions
        fuel_raw = experiment.fuel_material or (conditions.fuel_material if conditions else None)
        fuel = (fuel_raw or "").strip().lower() or None
        gravity = ((conditions.gravity_condition or "").strip().lower() if conditions else "") or None
        if conditions is None or conditions.oxygen_concentration is None:
            oxygen = None
        else:
            oxygen = f"{conditions.oxygen_concentration}|{(conditions.oxygen_unit or '').strip().lower()}|{(conditions.oxygen_basis or '').strip().lower()}"
        if conditions is None or conditions.ambient_pressure is None:
            pressure = None
        else:
            pressure = f"{conditions.ambient_pressure}|{(conditions.pressure_unit or '').strip().lower()}"
        if conditions is None or conditions.temperature is None:
            temperature = None
        else:
            temperature = f"{conditions.temperature}|{(conditions.temperature_unit or '').strip().lower()}"
        if conditions is None or conditions.airflow_velocity is None:
            airflow = None
        else:
            airflow = f"{conditions.airflow_velocity}|{(conditions.airflow_unit or '').strip().lower()}|{(conditions.airflow_direction or '').strip().lower()}"
        sample_raw = experiment.sample_geometry or (conditions.sample_geometry if conditions else None)
        sample = (sample_raw or "").strip().lower() or None
        return {
            "fuel material": fuel,
            "gravity condition": gravity,
            "oxygen condition": oxygen,
            "pressure": pressure,
            "temperature": temperature,
            "airflow": airflow,
            "sample geometry": sample,
        }

    def _condition_issues(self, experiments: list[Experiment]) -> list[str]:
        issues = []
        keys = [self._condition_keys(experiment) for experiment in experiments]
        for name in ["fuel material", "gravity condition", "oxygen condition", "pressure", "temperature", "airflow", "sample geometry"]:
            values = [item[name] for item in keys]
            if any(value is None for value in values):
                issues.append(f"{name} is not documented for every experiment")
            elif len(set(values)) > 1:
                issues.append(f"{name} differs across experiments")
        return issues

    def _conditions_summary(self, experiments: list[Experiment]) -> str | None:
        keys = [self._condition_keys(experiment) for experiment in experiments]
        parts = []
        for name in ["fuel material", "gravity condition", "oxygen condition", "pressure", "temperature", "airflow", "sample geometry"]:
            values = [item[name] for item in keys]
            shown = sorted({value for value in values if value is not None})
            if len(shown) > 1:
                parts.append(f"{name}: {' vs '.join(shown)}")
        return "; ".join(parts) if parts else None

    def _parameter_status(self, values: list[ComparedValue], condition_issues: list[str]) -> tuple[ComparabilityStatus, str]:
        present = [value for value in values if value.value is not None]
        if not present:
            return ComparabilityStatus.INSUFFICIENT_DATA, "No documented value for this parameter in any selected item."
        units = {value.unit for value in present if value.unit}
        if len(units) > 1:
            return ComparabilityStatus.NOT_COMPARABLE, f"Units differ ({', '.join(sorted(units))}); units are never converted."
        if any(value.unit is None for value in present):
            return ComparabilityStatus.NOT_COMPARABLE, "A documented value has no unit; values without units cannot be compared."
        kinds = {value.measurement_kind for value in present if value.measurement_kind}
        if len(kinds) > 1:
            return ComparabilityStatus.PARTIALLY_COMPARABLE, f"Measurement kinds differ ({', '.join(sorted(kinds))}); measured, derived and interpreted values are not directly comparable."
        methods = {value.measurement_method for value in present if value.measurement_method}
        if len(methods) > 1:
            return ComparabilityStatus.PARTIALLY_COMPARABLE, "Measurement methods differ; results may not be directly comparable."
        types = {type(value.value).__name__ for value in present}
        if len(types) > 1:
            return ComparabilityStatus.NOT_COMPARABLE, "Value types differ; values of different types cannot be compared."
        if len(present) < len(values):
            return ComparabilityStatus.PARTIALLY_COMPARABLE, "Value missing for at least one selected item; missing values are not treated as zero."
        if condition_issues:
            return ComparabilityStatus.PARTIALLY_COMPARABLE, "Experimental conditions differ: " + "; ".join(condition_issues) + "."
        return ComparabilityStatus.COMPARABLE, "Same unit, measurement kind and method, and matching experimental conditions."

    def _measurement_value(self, experiment: Experiment, parameter_name: str) -> tuple[ComparedValue, int]:
        matches = [m for m in (experiment.measurements or []) if (m.parameter_name or "").strip().lower() == parameter_name.strip().lower()]
        if not matches:
            return ComparedValue(item_id=experiment.id, value=None, missing_reason=f"No measurement named '{parameter_name}' documented for this experiment."), 0
        measurement = matches[0]
        return ComparedValue(
            item_id=experiment.id,
            value=measurement.value,
            unit=measurement.unit,
            measurement_kind=self._enum_value(measurement.measurement_kind),
            measurement_method=measurement.measurement_method,
            sensor=measurement.sensor,
            time_point=str(measurement.time_point) if measurement.time_point is not None else None,
            source_id=measurement.source_id,
            verification_status=self._enum_value(measurement.verification_status),
        ), len(matches)

    def _condition_rows(self, experiments: list[Experiment]) -> list[ConditionComparison]:
        specs = [
            ("fuel_material", ComparisonCategory.FUEL_MATERIAL, lambda e: ((e.fuel_material or (e.conditions.fuel_material if e.conditions else None)), None)),
            ("oxygen_concentration", ComparisonCategory.OXYGEN_CONDITION, lambda e: ((e.conditions.oxygen_concentration if e.conditions else None), (e.conditions.oxygen_unit if e.conditions else None))),
            ("ambient_pressure", ComparisonCategory.PRESSURE_CONDITION, lambda e: ((e.conditions.ambient_pressure if e.conditions else None), (e.conditions.pressure_unit if e.conditions else None))),
            ("temperature", ComparisonCategory.TEMPERATURE_CONDITION, lambda e: ((e.conditions.temperature if e.conditions else None), (e.conditions.temperature_unit if e.conditions else None))),
            ("airflow_velocity", ComparisonCategory.AIRFLOW_CONDITION, lambda e: ((e.conditions.airflow_velocity if e.conditions else None), (e.conditions.airflow_unit if e.conditions else None))),
            ("gravity_condition", ComparisonCategory.GRAVITY_CONDITION, lambda e: ((e.conditions.gravity_condition if e.conditions else None), None)),
            ("sample_geometry", ComparisonCategory.EXPERIMENT, lambda e: ((e.sample_geometry or (e.conditions.sample_geometry if e.conditions else None)), None)),
        ]
        rows = []
        for name, category, getter in specs:
            values = []
            for experiment in experiments:
                raw_value, raw_unit = getter(experiment)
                if raw_value is None or (isinstance(raw_value, str) and not raw_value.strip()):
                    values.append(ComparedValue(item_id=experiment.id, value=None, missing_reason=f"No documented {name} for this experiment."))
                else:
                    values.append(ComparedValue(item_id=experiment.id, value=raw_value, unit=raw_unit))
            present = [value for value in values if value.value is not None]
            if not present:
                status = ComparabilityStatus.INSUFFICIENT_DATA
                reason = f"No documented {name} in any selected experiment."
            elif len(present) < len(values):
                status = ComparabilityStatus.PARTIALLY_COMPARABLE
                reason = f"{name} is missing for at least one selected experiment."
            elif len({str(value.value) for value in present}) > 1:
                status = ComparabilityStatus.PARTIALLY_COMPARABLE
                reason = f"{name} differs across experiments."
            else:
                status = ComparabilityStatus.COMPARABLE
                reason = f"{name} is the same across all selected experiments."
            rows.append(ConditionComparison(condition_name=name, status=status, reason=reason, values=values))
        return rows

    def _summarize_rows(self, rows, item_ids, value_formatter):
        similarities = []
        differences = []
        missing = []
        incompatible = []
        for row in rows:
            name = getattr(row, "parameter_name", None) or getattr(row, "condition_name", "")
            present = [value for value in row.values if value.value is not None]
            for value in row.values:
                if value.value is None:
                    missing.append(f"{name}: no documented value for {value.item_id}.")
            if row.status == ComparabilityStatus.NOT_COMPARABLE:
                incompatible.append(f"{name}: {row.reason}")
            elif row.status == ComparabilityStatus.COMPARABLE and present and len({str(value.value) for value in present}) == 1:
                similarities.append(f"{name} is the same across all selected items ({value_formatter(present[0])}).")
            elif present:
                shown = ", ".join(f"{value.item_id} {value_formatter(value)}" for value in row.values)
                differences.append(f"{name} differs: {shown}.")
        return similarities, differences, missing, incompatible

    def _explain(self, rows, label: str) -> str:
        counts = {status: 0 for status in ComparabilityStatus}
        for row in rows:
            counts[row.status] += 1
        return (
            f"Compared {label} across {counts[ComparabilityStatus.COMPARABLE]} comparable, "
            f"{counts[ComparabilityStatus.PARTIALLY_COMPARABLE]} partially comparable, "
            f"{counts[ComparabilityStatus.NOT_COMPARABLE]} not comparable, and "
            f"{counts[ComparabilityStatus.INSUFFICIENT_DATA]} insufficient-data parameters. "
            "This comparison describes documented differences only; it does not claim causation."
        )

    def compare_experiments(self, experiment_ids: list[str], parameters: list[str] | None = None, include_conditions: bool = True) -> ExperimentComparison:
        cleaned = self._clean_ids(experiment_ids, "experiment")
        experiments = self._resolve_experiments(cleaned)
        all_params = sorted({m.parameter_name for e in experiments for m in (e.measurements or []) if m.parameter_name})
        if parameters is not None:
            wanted = [p.strip() for p in parameters if p and p.strip()]
            if not wanted:
                raise ValueError("parameters must not be empty when provided")
            known = {name.lower() for name in all_params}
            unknown = [name for name in wanted if name.lower() not in known]
            if unknown:
                raise ValueError("Unknown parameters: " + ", ".join(unknown))
            selected = wanted
        else:
            selected = all_params
        issues = self._condition_issues(experiments)
        summary = self._conditions_summary(experiments)
        rows = []
        for name in selected:
            values = []
            multi = []
            for experiment in experiments:
                compared, count = self._measurement_value(experiment, name)
                values.append(compared)
                if count > 1:
                    multi.append(f"{experiment.id} has {count} measurements named '{name}'; the first was used")
            status, reason = self._parameter_status(values, issues)
            if multi:
                reason = reason + " " + " ".join(multi) + "."
            rows.append(ParameterComparison(parameter_name=name, category=ComparisonCategory.MEASUREMENT, status=status, reason=reason, values=values, units=sorted({value.unit for value in values if value.unit}), conditions_note=summary))
        conditions = self._condition_rows(experiments) if include_conditions else []
        similarities, differences, missing, incompatible = self._summarize_rows(rows, [e.id for e in experiments], lambda v: self._format(v.value, v.unit))
        cond_similarities, cond_differences, cond_missing, _ = self._summarize_rows(conditions, [e.id for e in experiments], lambda v: self._format(v.value, v.unit))
        similarities.extend(cond_similarities)
        differences.extend(cond_differences)
        missing.extend(cond_missing)
        source_ids = sorted({source for e in experiments for source in (e.source_ids or [])} | {m.source_id for e in experiments for m in (e.measurements or []) if m.source_id})
        limitations = [LIMITATION_NO_CAUSATION, LIMITATION_NO_CONVERSION, LIMITATION_MISSING_NOT_ZERO]
        if issues:
            limitations.append("Experimental conditions differ or are incomplete: " + "; ".join(issues) + ".")
        if not selected:
            limitations.append("No documented measurements were found in the selected experiments.")
        return ExperimentComparison(
            comparison_id="cmp-exp-" + "-".join(sorted(e.id for e in experiments)),
            experiment_ids=[e.id for e in experiments],
            parameters=rows,
            conditions=conditions,
            similarities=similarities,
            differences=differences,
            missing_information=missing,
            incompatible_items=incompatible,
            source_ids=source_ids,
            explanation=self._explain(rows + conditions, "experiments"),
            limitations=limitations,
            methodology=METHODOLOGY_EXPERIMENTS,
        )

    def compare_hardware(self, hardware_ids: list[str], fields: list[str] | None = None) -> HardwareComparison:
        cleaned = self._clean_ids(hardware_ids, "hardware")
        items = self._resolve_hardware(cleaned)
        allowed = {"hardware_type", "facility_classification", "purpose", "parent_hardware_id", "name"}
        wanted = fields if fields is not None else ["hardware_type", "facility_classification", "purpose", "parent_hardware_id"]
        if not wanted:
            raise ValueError("fields must not be empty when provided")
        unknown = [name for name in wanted if name not in allowed]
        if unknown:
            raise ValueError("Unknown fields: " + ", ".join(unknown))
        rows = []
        for field_name in wanted:
            values = []
            for hardware in items:
                raw = getattr(hardware, field_name, None)
                raw = self._enum_value(raw)
                if raw is None or (isinstance(raw, str) and not raw.strip()):
                    values.append(ComparedValue(item_id=hardware.id, value=None, missing_reason=f"No documented {field_name} for this hardware."))
                else:
                    values.append(ComparedValue(item_id=hardware.id, value=str(raw)))
            present = [value for value in values if value.value is not None]
            if not present:
                status = ComparabilityStatus.INSUFFICIENT_DATA
                reason = f"No documented {field_name} in any selected hardware."
            elif len(present) < len(values):
                status = ComparabilityStatus.PARTIALLY_COMPARABLE
                reason = f"{field_name} is missing for at least one selected hardware item."
            elif len({str(value.value) for value in present}) > 1:
                status = ComparabilityStatus.PARTIALLY_COMPARABLE
                reason = f"{field_name} differs across selected hardware."
            else:
                status = ComparabilityStatus.COMPARABLE
                reason = f"{field_name} is the same across all selected hardware."
            rows.append(ParameterComparison(parameter_name=field_name, category=ComparisonCategory.HARDWARE, status=status, reason=reason, values=values, units=[]))
        types = [self._enum_value(hardware.hardware_type) for hardware in items]
        same_type = len(set(types)) == 1
        supported = [set(hardware.supported_measurements or []) for hardware in items]
        shared = sorted(set.intersection(*supported)) if supported else []
        unique = {hardware.id: sorted(set(hardware.supported_measurements or []) - set(shared)) for hardware in items}
        similarities, differences, missing, incompatible = self._summarize_rows(rows, [h.id for h in items], lambda v: self._format(v.value, v.unit))
        if shared:
            similarities.append(f"Supported measurements shared by all selected hardware: {', '.join(shared)}.")
        shared_experiments = set.intersection(*[set(hardware.related_experiment_ids or []) for hardware in items]) if items else set()
        if shared_experiments:
            similarities.append(f"Related experiments shared by all selected hardware: {', '.join(sorted(shared_experiments))}.")
        source_ids = sorted({source for h in items for source in (h.source_ids or [])})
        limitations = [LIMITATION_NO_CAUSATION, LIMITATION_MISSING_NOT_ZERO, "This comparison does not rank hardware by performance, safety, or effectiveness."]
        if not same_type:
            limitations.append(f"Hardware types differ ({', '.join(sorted(set(types)))}); different types serve different purposes and are not directly interchangeable.")
        return HardwareComparison(
            comparison_id="cmp-hw-" + "-".join(sorted(h.id for h in items)),
            hardware_ids=[h.id for h in items],
            hardware_types=sorted(set(types)),
            same_hardware_type=same_type,
            fields=rows,
            shared_measurements=shared,
            unique_measurements=unique,
            similarities=similarities,
            differences=differences,
            missing_information=missing,
            source_ids=source_ids,
            explanation=self._explain(rows, "hardware items"),
            limitations=limitations,
            methodology=METHODOLOGY_HARDWARE,
        )

    def compare_measurements(self, measurement_ids: list[str], parameter_names: list[str] | None = None) -> MeasurementComparison:
        cleaned = self._clean_ids(measurement_ids, "measurement")
        found = [self._find_measurement(item_id) for item_id in cleaned]
        parents = []
        for _, experiment in found:
            if experiment.id not in [item.id for item in parents]:
                parents.append(experiment)
        all_params = sorted({m.parameter_name for m, _ in found if m.parameter_name})
        if parameter_names is not None:
            wanted = [p.strip() for p in parameter_names if p and p.strip()]
            if not wanted:
                raise ValueError("parameter_names must not be empty when provided")
            known = {name.lower() for name in all_params}
            unknown = [name for name in wanted if name.lower() not in known]
            if unknown:
                raise ValueError("Unknown parameters: " + ", ".join(unknown))
            selected = wanted
        else:
            selected = all_params
        issues = self._condition_issues(parents)
        summary = self._conditions_summary(parents)
        rows = []
        for name in selected:
            values = []
            for measurement, experiment in found:
                if (measurement.parameter_name or "").strip().lower() != name.strip().lower():
                    values.append(ComparedValue(item_id=measurement.id, value=None, missing_reason=f"This measurement does not document parameter '{name}'."))
                    continue
                values.append(ComparedValue(
                    item_id=measurement.id,
                    value=measurement.value,
                    unit=measurement.unit,
                    measurement_kind=self._enum_value(measurement.measurement_kind),
                    measurement_method=measurement.measurement_method,
                    sensor=measurement.sensor,
                    time_point=str(measurement.time_point) if measurement.time_point is not None else None,
                    source_id=measurement.source_id,
                    verification_status=self._enum_value(measurement.verification_status),
                ))
            status, reason = self._parameter_status(values, issues)
            rows.append(ParameterComparison(parameter_name=name, category=ComparisonCategory.MEASUREMENT, status=status, reason=reason, values=values, units=sorted({value.unit for value in values if value.unit}), conditions_note=summary))
        similarities, differences, missing, incompatible = self._summarize_rows(rows, [m.id for m, _ in found], lambda v: self._format(v.value, v.unit))
        source_ids = sorted({m.source_id for m, _ in found if m.source_id} | {source for _, e in found for source in (e.source_ids or [])})
        limitations = [LIMITATION_NO_CAUSATION, LIMITATION_NO_CONVERSION, LIMITATION_MISSING_NOT_ZERO]
        if issues:
            limitations.append("Parent experimental conditions differ or are incomplete: " + "; ".join(issues) + ".")
        return MeasurementComparison(
            comparison_id="cmp-meas-" + "-".join(sorted(m.id for m, _ in found)),
            measurement_ids=[m.id for m, _ in found],
            parameters=rows,
            similarities=similarities,
            differences=differences,
            missing_information=missing,
            incompatible_items=incompatible,
            source_ids=source_ids,
            explanation=self._explain(rows, "measurements"),
            limitations=limitations,
            methodology=METHODOLOGY_MEASUREMENTS,
        )
