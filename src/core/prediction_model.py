from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.core.types import GhiSlot


class PredictionModel(ABC):
    @abstractmethod
    async def train(self, training_data: list[GhiSlot]) -> None:
        pass

    @abstractmethod
    async def forecast(self, timestamp: datetime, latitude: float, longitude: float) -> float:
        pass
