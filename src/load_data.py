from __future__ import annotations

import httpx

from src.core.data_downloader import list_historic_datasets, load_historic
from src.core.types import GhiSlot


def load_training_data() -> list[GhiSlot]:
    with httpx.Client(timeout=60.0) as client:
        datasets = list_historic_datasets(client)
        historics = [load_historic(dataset.id, client) for dataset in datasets]
    return [slot for historic in historics for slot in historic.slots]
