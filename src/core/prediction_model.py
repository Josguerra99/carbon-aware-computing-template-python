from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .types import GhiSlot


class PredictionModel(ABC):
    @abstractmethod
    def train(self, training_data: list[GhiSlot]) -> None:
        pass

    @abstractmethod
    def forecast(self, timestamp: datetime, latitude: float, longitude: float) -> float:
        pass
