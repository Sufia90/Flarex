from pathlib import Path
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/flammability", tags=["flammability"])

MODEL_PATH = Path(__file__).resolve().parents[3] / "model_backend.json"


def _load_model():
    with open(MODEL_PATH, encoding="utf-8") as f:
        return json.load(f)


MODEL = _load_model()


class PredictRequest(BaseModel):
    oxygen_pct: float = Field(..., ge=10.0, le=25.0)
    airflow_cms: float = Field(10.0, ge=0.0, le=40.0)
    material: str = "PMMA"
    form: str | None = None
    pressure_kpa: float = 101.3


class PredictionValue(BaseModel):
    value: float
    unit: str
    confidence_pct: float
    shown_as: str


class PredictResponse(BaseModel):
    regime: str
    regime_basis: str
    predictions: dict[str, PredictionValue]
    explanation: dict
    warnings: list[str]


def _walk(nodes, x):
    i = 0
    while nodes[i]["feature"] != -2:
        n = nodes[i]
        i = n["left"] if x[n["feature"]] <= n["threshold"] else n["right"]
    return nodes[i]["value"], nodes[i]["std"]


def _features(oxygen, fan, air, co2i, coi, material, form):
    return ([oxygen, fan, air, co2i, coi]
            + [1.0 if material == m else 0.0 for m in MODEL["materials"]]
            + [1.0 if form == f else 0.0 for f in MODEL["forms"]])


def _confidence(r2, leaf_std, overall_std):
    c = 1.0 - (leaf_std / overall_std if overall_std else 0.0)
    c = max(0.0, min(1.0, c))
    return round(max(0.0, min(1.0, r2)) * c * 100, 1)


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    material = req.material
    if material not in MODEL["materials"]:
        raise HTTPException(status_code=400, detail="Unknown material. Allowed: " + ", ".join(MODEL["materials"]))
    form = req.form
    if form is None:
        form = "film" if material == "PMMA" else "other"
    if form not in MODEL["forms"]:
        raise HTTPException(status_code=400, detail="Unknown form. Allowed: " + ", ".join(MODEL["forms"]))
    med = MODEL["pmma_medians"] if material == "PMMA" else MODEL["medians"]
    air = max(0.0, min(10.0, req.airflow_cms / 4.0))
    x = _features(req.oxygen_pct, med["fan"], air, med["co2i"], med["coi"], material, form)
    warnings = []
    if req.oxygen_pct < 13.6 or req.oxygen_pct > 22.2:
        warnings.append("Oxygen is outside the tested range 13.6 to 22.2 percent, so this prediction is extrapolated.")
    if req.pressure_kpa != 101.3:
        warnings.append("Pressure is fixed at 101.3 kPa in the training data and does not change the prediction.")
    warnings.append("Airflow is converted from cm/s to the instrument setting by air = cm/s divided by 4, an estimate, because the table records instrument settings, not a calibrated cm/s conversion.")
    warnings.append("This is a rough estimate from 129 BASS-II tests, not a precise prediction.")
    regime = "sooty flame" if req.oxygen_pct >= 19.0 else "blue flame"
    units = {"final_o2": "%", "final_co": "ppm", "final_co2": "%"}
    labels = {"final_o2": "Final O2", "final_co": "Final CO", "final_co2": "Final CO2"}
    preds = {}
    for tname, target in MODEL["targets"].items():
        value, leaf_std = _walk(target["nodes"], x)
        conf = _confidence(target["r2"], leaf_std, target["overall_std"])
        if conf < 25.0:
            warnings.append(f"{labels[tname]} prediction has {conf}% confidence and is unreliable. The model cannot reliably predict {labels[tname]} from these inputs.")
        preds[tname] = PredictionValue(
            value=round(value, 3),
            unit=units[tname],
            confidence_pct=conf,
            shown_as="model-estimated",
        )
    demo = MODEL["killer_demo_nearest"]
    explanation = {
        "finding": "Lower oxygen delays soot formation in PMMA. At 17 percent oxygen and 10 to 12 cm/s flow, a 2 cm PMMA sphere burns with a predominantly blue flame.",
        "finding_source": "src-bass-np-2015",
        "nearest_tests_above_19pct_o2": demo["nearest_above_19pct"],
        "nearest_tests_below_19pct_o2": demo["nearest_below_19pct"],
        "model": MODEL["model"],
        "metrics": {t: {"mae": v["mae"], "r2": v["r2"]} for t, v in MODEL["targets"].items()},
    }
    return PredictResponse(
        regime=regime,
        regime_basis="Interpretation of the published BASS finding, not a learned label. Boundary at 19 percent oxygen, the midpoint of the documented 21 and 17 percent.",
        predictions=preds,
        explanation=explanation,
        warnings=warnings,
    )


@router.get("/model-info")
def model_info():
    return {
        "model": MODEL["model"],
        "materials": MODEL["materials"],
        "forms": MODEL["forms"],
        "targets": {t: {"mae": v["mae"], "r2": v["r2"]} for t, v in MODEL["targets"].items()},
        "regime_rule": MODEL["regime_rule"],
        "confidence_rule": MODEL["confidence_rule"],
        "training_rows": 129,
        "training_source": "BASS-II PSI-25 experimental table",
    }
