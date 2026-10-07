"""Copia este archivo a src/workshop/ para probarlo (src/workshop/ no va a git)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from src.core.math_helper import create_linear_regression, solar_hour
from src.core.prediction_model import PredictionModel
from src.core.types import GhiSlot


class LinearRegressionGlobal(PredictionModel):
    def __init__(self) -> None:
        self._predict: Callable[[float], float] | None = None

    def train(self, training_data: list[GhiSlot]) -> None:
        points = [(slot.time.timestamp() * 1000, slot.ghi_wm2) for slot in training_data]
        self._predict = create_linear_regression(points)

    def forecast(self, timestamp: datetime, latitude: float, longitude: float) -> float:
        if self._predict is None:
            raise RuntimeError("Model not trained")
        return max(0.0, self._predict(float(solar_hour(timestamp, longitude))))
