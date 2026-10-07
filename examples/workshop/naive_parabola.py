"""Copia este archivo a src/workshop/ para probarlo (src/workshop/ no va a git)."""

from __future__ import annotations

from datetime import datetime

from src.core.math_helper import create_parabola, solar_hour
from src.core.prediction_model import PredictionModel
from src.core.types import GhiSlot


class NaiveParabola(PredictionModel):
    START_HOUR_OF_DAY = 5
    END_HOUR_OF_DAY = 19
    MAX_KWH_PER_DAY = 1000

    def __init__(self) -> None:
        self._parabola = create_parabola(
            NaiveParabola.MAX_KWH_PER_DAY,
            NaiveParabola.START_HOUR_OF_DAY,
            NaiveParabola.END_HOUR_OF_DAY,
        )

    def train(self, training_data: list[GhiSlot]) -> None:
        pass

    def forecast(self, timestamp: datetime, latitude: float, longitude: float) -> float:
        return max(0.0, self._parabola(float(solar_hour(timestamp, longitude))))
