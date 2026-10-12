from __future__ import annotations

from src.core.historic_store import historic_store
from src.core.types import GhiHistoric, HistoricDatasetInfo


class DataDownloader:
    """@deprecated Use historic_store.get_train / get_meta."""

    @staticmethod
    async def list_historic_datasets() -> list[HistoricDatasetInfo]:
        return await historic_store.list_datasets()

    @staticmethod
    async def load_historic(dataset_id: str) -> GhiHistoric:
        return await historic_store.get_train(dataset_id)
