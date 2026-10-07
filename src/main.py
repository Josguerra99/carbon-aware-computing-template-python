from __future__ import annotations

from datetime import datetime

from src.core.prediction_model import PredictionModel
from src.core.types import GhiSlot


class SimplePredictionModel(PredictionModel):
    """
    Implementa aquí tu modelo del taller.
    `train` se llama una vez al arrancar el servidor.
    `forecast` recibe timestamp UTC más lat/lon del dataset pedido.
    """

    def train(self, training_data: list[GhiSlot]) -> None:
        pass

    def forecast(self, timestamp: datetime, latitude: float, longitude: float) -> float:
        return 0.0


# Cambia esta línea cuando copies soluciones a src/workshop/ (carpeta ignorada por git).
workshop_model: PredictionModel = SimplePredictionModel()

# Ejemplo:
# from src.workshop.linear_regression import LinearRegressionGlobal
# workshop_model = LinearRegressionGlobal()
