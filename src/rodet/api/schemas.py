from __future__ import annotations

from pydantic import BaseModel, Field


class TrainResponse(BaseModel):
    ok: bool
    n_samples: int
    n_classes: int
    classes: list[str]


class PredictRequest(BaseModel):
    text: str = Field(min_length=3, description="Consulta del usuario (presupuesto + preferencias en texto).")


class TopPrediction(BaseModel):
    label: str
    probability: float


class PredictResponse(BaseModel):
    ok: bool
    top5: list[TopPrediction]