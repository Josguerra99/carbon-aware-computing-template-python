from __future__ import annotations

from datetime import datetime

from src.core.prediction_model import PredictionModel
from src.core.types import GhiSlot


class MyPredictionModel(PredictionModel):
    async def train(self, training_data: list[GhiSlot]) -> None:
        pass

    async def forecast(self, timestamp: datetime, latitude: float, longitude: float) -> float:
        return 0.0


workshop_model = MyPredictionModel()
