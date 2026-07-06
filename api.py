"""Production prediction API for EduPath AI."""

from __future__ import annotations

import logging
import os
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from decision_engine import generate_career_recommendations

ROOT_DIR = Path(__file__).resolve().parent
MODEL_DIR = Path(os.getenv("MODEL_DIR", ROOT_DIR / "models"))
MODEL_PATHS = {
    "placement": MODEL_DIR / "placement_model.joblib",
    "backlog": MODEL_DIR / "backlog_risk_model.joblib",
    "exam": MODEL_DIR / "exam_readiness_model.joblib",
}
logger = logging.getLogger("edupath.api")
models: dict[str, Any] = {}
explanation_baselines: dict[str, Any] = {}

Percentage = Annotated[float, Field(ge=0, le=100)]
Cgpa = Annotated[float, Field(ge=0, le=10)]
Backlogs = Annotated[int, Field(ge=0, le=50)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlacementRequest(StrictModel):
    attendance: Percentage
    cgpa: Cgpa
    aptitude_score: Percentage
    coding_score: Percentage
    communication_score: Percentage
    mock_exam_score: Percentage
    backlogs: Backlogs
    career_interest: str = Field(min_length=1, max_length=100)


class BacklogRiskRequest(StrictModel):
    attendance: Percentage
    cgpa: Cgpa
    aptitude_score: Percentage
    coding_score: Percentage
    communication_score: Percentage
    mock_exam_score: Percentage


class ExamReadinessRequest(StrictModel):
    attendance: Percentage
    cgpa: Cgpa
    aptitude_score: Percentage
    mock_exam_score: Percentage
    backlogs: Backlogs
    exam_selected: str = Field(min_length=1, max_length=100)


class StudentPredictionRequest(StrictModel):
    name: str | None = Field(default=None, max_length=100)
    degree: str | None = Field(default=None, max_length=100)
    branch: str | None = Field(default=None, max_length=100)
    semester: int | None = Field(default=None, ge=1, le=12)
    primary_goal: str | None = Field(default=None, max_length=100)
    goal_context: dict[str, str | int | float | bool] = Field(default_factory=dict)
    attendance: Percentage
    cgpa: Cgpa
    aptitude_score: Percentage
    coding_score: Percentage
    communication_score: Percentage
    mock_exam_score: Percentage
    backlogs: Backlogs
    career_interest: str = Field(default="Undecided", min_length=1, max_length=100)
    exam_selected: str = Field(min_length=1, max_length=100)


class ClassPrediction(BaseModel):
    prediction: str
    confidence: float
    probabilities: dict[str, float]
    explanation_method: str
    factors: list["FeatureImpact"]


class FeatureImpact(BaseModel):
    feature: str
    value: str
    baseline: str
    effect: Literal["supports", "opposes", "neutral"]
    probability_change: float
    reason: str


class BacklogRiskPrediction(ClassPrediction):
    prediction: Literal["Low Risk", "High Risk"]


class CareerFit(BaseModel):
    career: str
    fit_score: float


class RoadmapStep(BaseModel):
    phase: str
    timeline: str
    focus: str
    actions: list[str]
    success_metric: str


class StudentRoadmap(BaseModel):
    recommended_path: str
    fit_score: float
    summary: str
    strengths: list[str]
    priority_gaps: list[str]
    alternative_paths: list[CareerFit]
    steps: list[RoadmapStep]


class CareerRecommendation(BaseModel):
    career: str
    suitability_score: float
    confidence: float
    why_recommended: str
    pros: list[str]
    challenges: list[str]
    future_demand: str
    salary_range: str
    required_skills: list[str]
    missing_skills: list[str]
    time_to_job_ready: str
    roadmap: list[str]


class CombinedPrediction(BaseModel):
    placement: ClassPrediction
    backlog_risk: BacklogRiskPrediction
    exam_readiness: ClassPrediction
    roadmap: StudentRoadmap
    career_recommendations: list[CareerRecommendation]


def _load_models() -> None:
    missing = [str(path) for path in MODEL_PATHS.values() if not path.exists()]
    if missing:
        raise RuntimeError(f"Required model artifacts are missing: {missing}")
    for name, path in MODEL_PATHS.items():
        models[name] = joblib.load(path)
        logger.info("Loaded %s model from %s", name, path)
    baseline_path = MODEL_DIR / "explanation_baselines.json"
    if not baseline_path.exists():
        raise RuntimeError(f"Explanation baseline artifact is missing: {baseline_path}")
    explanation_baselines.update(
        json.loads(baseline_path.read_text(encoding="utf-8"))["values"]
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    _load_models()
    yield
    models.clear()
    explanation_baselines.clear()


app = FastAPI(
    title="EduPath AI API",
    description="Student placement, backlog-risk, and exam-readiness predictions.",
    version="1.0.0",
    lifespan=lifespan,
)

# Read external assistant/LLM API key from environment (do NOT commit your key).
# Set `GEMINI_API_KEY` in your shell or an untracked `.env` file before starting the server.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
app.state.gemini_api_key = GEMINI_API_KEY

UPLOAD_DIR = ROOT_DIR / "uploads"


@app.post("/api/v1/documents/upload", tags=["documents"])
async def upload_document(file: UploadFile = File(...)) -> dict[str, str | int]:
    """Accept and persist uploaded documents to the local uploads folder."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / file.filename
    contents = await file.read()
    dest.write_bytes(contents)
    return {"filename": file.filename, "size": dest.stat().st_size}


@app.get("/api/v1/documents", tags=["documents"])
def list_documents() -> dict[str, list[str]]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files = [p.name for p in sorted(UPLOAD_DIR.iterdir()) if p.is_file()]
    return {"files": files}


@app.post("/api/v1/assistant", tags=["assistant"])
def assistant(message: dict) -> dict:
    """Lightweight assistant endpoint. If `profile` is provided, return top career recaps."""
    text = message.get("text", "")
    profile = message.get("profile")
    has_external_llm = bool(app.state.gemini_api_key)
    if profile and isinstance(profile, dict):
        try:
            recs = generate_career_recommendations(profile)
            top = recs[0] if recs else None
            return {
                "reply": f"I reviewed the profile. Top recommendation: {top['career']} ({top['suitability_score']}%).",
                "recommendations": recs,
                "external_llm": has_external_llm,
            }
        except Exception:
            return {"reply": "I couldn't generate recommendations from the provided profile.", "external_llm": has_external_llm}
    return {"reply": f"Echo: {text}", "external_llm": has_external_llm}

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        (
            "http://localhost:3000,http://127.0.0.1:3000,"
            "http://localhost:5173,http://127.0.0.1:5173"
        ),
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


FEATURE_LABELS = {
    "attendance": "Attendance",
    "cgpa": "CGPA",
    "aptitude_score": "Aptitude score",
    "coding_score": "Coding score",
    "communication_score": "Communication score",
    "mock_exam_score": "Mock exam score",
    "backlogs": "Backlogs",
    "career_interest": "Career interest",
    "exam_selected": "Selected exam",
}


def _format_factor_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _local_factors(
    model: Any,
    frame: pd.DataFrame,
    predicted_class: Any,
    current_probability: float,
) -> list[FeatureImpact]:
    """Measure local probability sensitivity by replacing one input at a time."""
    class_index = list(model.classes_).index(predicted_class)
    factors: list[FeatureImpact] = []
    for feature in frame.columns:
        if feature not in explanation_baselines:
            continue
        baseline = explanation_baselines[feature]
        comparison_values = frame.iloc[0].to_dict()
        comparison_values[feature] = baseline
        comparison = pd.DataFrame([comparison_values])
        baseline_probability = float(model.predict_proba(comparison)[0][class_index])
        delta = current_probability - baseline_probability
        effect: Literal["supports", "opposes", "neutral"]
        if delta > 0.005:
            effect = "supports"
        elif delta < -0.005:
            effect = "opposes"
        else:
            effect = "neutral"
        label = FEATURE_LABELS.get(feature, feature.replace("_", " ").title())
        points = abs(delta) * 100
        reason = (
            f"Changing {label.lower()} to the training baseline changes this "
            f"prediction by {points:.1f} percentage points."
        )
        factors.append(
            FeatureImpact(
                feature=label,
                value=_format_factor_value(frame.iloc[0][feature]),
                baseline=_format_factor_value(baseline),
                effect=effect,
                probability_change=round(delta, 6),
                reason=reason,
            )
        )
    factors.sort(key=lambda factor: abs(factor.probability_change), reverse=True)
    return factors[:4]


def _predict(model_name: str, payload: dict[str, Any]) -> ClassPrediction:
    try:
        model = models[model_name]
        frame = pd.DataFrame([payload])
        raw_predicted_class = model.predict(frame)[0]
        predicted_class = str(raw_predicted_class)
        probabilities = model.predict_proba(frame)[0]
        probability_map = {
            str(label): round(float(probability), 6)
            for label, probability in zip(model.classes_, probabilities)
        }
        confidence = max(probability_map.values())
        return ClassPrediction(
            prediction=predicted_class,
            confidence=confidence,
            probabilities=probability_map,
            explanation_method="Local model sensitivity against training-data baselines",
            factors=_local_factors(
                model, frame, raw_predicted_class, float(max(probabilities))
            ),
        )
    except KeyError as exc:
        logger.exception("Model is unavailable: %s", model_name)
        raise HTTPException(status_code=503, detail="Prediction model is unavailable") from exc
    except Exception as exc:
        logger.exception("%s prediction failed", model_name)
        raise HTTPException(status_code=500, detail="Prediction failed") from exc


def _placement(payload: PlacementRequest) -> ClassPrediction:
    return _predict("placement", payload.model_dump())


def _backlog(payload: BacklogRiskRequest) -> BacklogRiskPrediction:
    result = _predict("backlog", payload.model_dump())
    label = "High Risk" if result.prediction == "1" else "Low Risk"
    probabilities = {
        "Low Risk": result.probabilities.get("0", 0.0),
        "High Risk": result.probabilities.get("1", 0.0),
    }
    return BacklogRiskPrediction(
        prediction=label,
        confidence=probabilities[label],
        probabilities=probabilities,
        explanation_method=result.explanation_method,
        factors=result.factors,
    )


def _exam(payload: ExamReadinessRequest) -> ClassPrediction:
    return _predict("exam", payload.model_dump())


CAREER_WEIGHTS = {
    "Software Engineer": {"coding_score": 0.45, "aptitude_score": 0.20, "cgpa": 0.15, "communication_score": 0.10, "attendance": 0.10},
    "Data Scientist": {"aptitude_score": 0.35, "coding_score": 0.30, "cgpa": 0.20, "communication_score": 0.10, "attendance": 0.05},
    "AI Researcher": {"cgpa": 0.30, "aptitude_score": 0.30, "coding_score": 0.25, "communication_score": 0.05, "attendance": 0.10},
    "Cybersecurity": {"coding_score": 0.35, "aptitude_score": 0.30, "attendance": 0.15, "cgpa": 0.10, "communication_score": 0.10},
    "Cloud Engineer": {"coding_score": 0.30, "aptitude_score": 0.25, "communication_score": 0.15, "attendance": 0.15, "cgpa": 0.15},
    "Business Analyst": {"communication_score": 0.40, "aptitude_score": 0.25, "cgpa": 0.15, "attendance": 0.15, "coding_score": 0.05},
}
SKILL_LABELS = {
    "attendance": "attendance consistency",
    "cgpa": "academic foundation",
    "aptitude_score": "quantitative aptitude",
    "coding_score": "coding and problem solving",
    "communication_score": "communication",
    "mock_exam_score": "exam performance",
}


def _build_roadmap(
    payload: StudentPredictionRequest,
    placement: ClassPrediction,
    backlog: BacklogRiskPrediction,
    exam: ClassPrediction,
) -> StudentRoadmap:
    values = payload.model_dump()
    normalized = {**values, "cgpa": payload.cgpa * 10}
    fits = []
    for career, weights in CAREER_WEIGHTS.items():
        score = sum(float(normalized[feature]) * weight for feature, weight in weights.items())
        fits.append(CareerFit(career=career, fit_score=round(score, 1)))
    fits.sort(key=lambda item: item.fit_score, reverse=True)
    recommended = fits[0]

    skill_scores = {
        "coding_score": payload.coding_score,
        "aptitude_score": payload.aptitude_score,
        "communication_score": payload.communication_score,
        "cgpa": payload.cgpa * 10,
        "attendance": payload.attendance,
        "mock_exam_score": payload.mock_exam_score,
    }
    ranked_skills = sorted(skill_scores.items(), key=lambda item: item[1], reverse=True)
    strengths = [SKILL_LABELS[key] for key, score in ranked_skills if score >= 75][:3]
    career_weights = CAREER_WEIGHTS[recommended.career]
    gap_candidates = sorted(
        (
            (key, (80 - skill_scores[key]) * weight)
            for key, weight in career_weights.items()
            if skill_scores[key] < 80
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    gaps = [SKILL_LABELS[key] for key, _ in gap_candidates][:3]
    if payload.backlogs > 0:
        gaps.insert(0, "backlog clearance")
    if not strengths:
        strengths = [SKILL_LABELS[ranked_skills[0][0]]]
    if not gaps:
        gaps = ["advanced portfolio depth"]

    primary_gap = gaps[0]
    exam_action = (
        f"Complete two timed {payload.exam_selected} mocks each week and review every error."
        if payload.exam_selected != "No exam"
        else "Use two weekly aptitude sessions to keep placement-test readiness high."
    )
    placement_action = (
        "Apply to 8–10 well-matched roles each week and track conversion by stage."
        if placement.prediction != "Not Placed"
        else "Delay mass applications for four weeks while closing the primary skill gap."
    )
    risk_action = (
        "Create a faculty-backed backlog recovery schedule before adding new commitments."
        if backlog.prediction == "High Risk" or payload.backlogs > 0
        else "Protect attendance and weekly revision so academic risk stays low."
    )

    return StudentRoadmap(
        recommended_path=recommended.career,
        fit_score=recommended.fit_score,
        summary=(
            f"{recommended.career} is the strongest current fit. Build around "
            f"{strengths[0]} while improving {primary_gap}; reassess after 90 days."
        ),
        strengths=strengths,
        priority_gaps=gaps,
        alternative_paths=fits[1:3],
        steps=[
            RoadmapStep(
                phase="Foundation",
                timeline="Weeks 1–4",
                focus=f"Close the {primary_gap} gap",
                actions=[risk_action, f"Schedule five focused hours per week for {primary_gap}."],
                success_metric=f"Raise the next measured {primary_gap} score by at least 10 points.",
            ),
            RoadmapStep(
                phase="Proof of skill",
                timeline="Weeks 5–8",
                focus=f"Build evidence for {recommended.career}",
                actions=[
                    f"Complete one portfolio project aligned with {recommended.career}.",
                    "Publish the project with a clear README, demo, and measurable outcome.",
                    exam_action,
                ],
                success_metric="Ship one review-ready project and complete four timed assessments.",
            ),
            RoadmapStep(
                phase="Launch",
                timeline="Weeks 9–12",
                focus="Convert readiness into opportunities",
                actions=[
                    placement_action,
                    "Practice two interviews per week and record recurring weak answers.",
                    "Update the resume with project evidence and role-specific keywords.",
                ],
                success_metric="Reach at least three interview or mentor-review conversations.",
            ),
        ],
    )


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"service": "EduPath AI API", "docs": "/docs"}


@app.get("/health", tags=["system"])
def health() -> dict[str, Any]:
    return {"status": "healthy", "models_loaded": sorted(models.keys())}


@app.post("/api/v1/predictions/placement", response_model=ClassPrediction, tags=["predictions"])
def predict_placement(payload: PlacementRequest) -> ClassPrediction:
    return _placement(payload)


@app.post("/api/v1/predictions/backlog-risk", response_model=BacklogRiskPrediction, tags=["predictions"])
def predict_backlog_risk(payload: BacklogRiskRequest) -> BacklogRiskPrediction:
    return _backlog(payload)


@app.post("/api/v1/predictions/exam-readiness", response_model=ClassPrediction, tags=["predictions"])
def predict_exam_readiness(payload: ExamReadinessRequest) -> ClassPrediction:
    return _exam(payload)


@app.post("/api/v1/predictions/student", response_model=CombinedPrediction, tags=["predictions"])
def predict_student(payload: StudentPredictionRequest) -> CombinedPrediction:
    values = payload.model_dump()
    placement = _placement(PlacementRequest(**{key: values[key] for key in PlacementRequest.model_fields}))
    backlog = _backlog(BacklogRiskRequest(**{key: values[key] for key in BacklogRiskRequest.model_fields}))
    exam = _exam(ExamReadinessRequest(**{key: values[key] for key in ExamReadinessRequest.model_fields}))
    career_recommendations = [
        CareerRecommendation(**recommendation)
        for recommendation in generate_career_recommendations(values)
    ]
    return CombinedPrediction(
        placement=placement,
        backlog_risk=backlog,
        exam_readiness=exam,
        roadmap=_build_roadmap(payload, placement, backlog, exam),
        career_recommendations=career_recommendations,
    )
