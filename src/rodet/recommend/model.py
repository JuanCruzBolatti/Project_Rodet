from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

ROOT_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT_DIR / "data"
MODEL_PATH = MODEL_DIR / "model.joblib"


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=50_000)),
            ("clf", LogisticRegression(max_iter=2000, solver="lbfgs")),
        ]
    )


@dataclass(frozen=True)
class TrainResult:
    n_samples: int
    n_classes: int
    classes: list[str]


def train_and_save(X_text: list[str], y: list[str]) -> TrainResult:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    pipe = build_pipeline()
    pipe.fit(X_text, y)
    joblib.dump(pipe, MODEL_PATH)

    classes = list(pipe.named_steps["clf"].classes_)
    return TrainResult(n_samples=len(X_text), n_classes=len(classes), classes=classes)


def load_model() -> Pipeline:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Train it first via /api/train.")
    return joblib.load(MODEL_PATH)