from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.core.historic_store import HistoricStore
from src.core.types import GhiSeriesJson
from src.core.workshop_client import DatasetMeta, WorkshopManifest


def _manifest(config_id: str, csv_bundle_hash: str = "abc") -> WorkshopManifest:
    return {
        "configId": config_id,
        "configName": config_id,
        "scenarioCount": 1,
        "datasetsHash": config_id,
        "csvBundleHash": csv_bundle_hash,
        "generatedAt": "2026-01-01T00:00:00.000Z",
    }


def _train(label: str) -> GhiSeriesJson:
    return {
        "datasetId": "mexico",
        "location": "CDMX",
        "latitude": 19.43,
        "longitude": -99.13,
        "unit": "W/m²",
        "source": label,
        "slots": [
            {
                "time": "2026-01-01T06:00:00.000Z",
                "ghiWm2": 10,
                "cloudCoverPct": None,
                "temperatureC": None,
            }
        ],
    }


class FakeClient:
    def __init__(self) -> None:
        self.config_id = "level-a"
        self.bundle = "csv-v1"
        self.train_fetches = 0

    async def fetch_manifest(self) -> WorkshopManifest:
        return _manifest(self.config_id, self.bundle)

    async def fetch_meta(self, dataset_id: str) -> DatasetMeta:
        return {"datasetId": dataset_id, "latitude": 19.43, "longitude": -99.13}

    async def fetch_train_series(self, dataset_id: str) -> GhiSeriesJson:
        self.train_fetches += 1
        return _train(self.config_id if self.bundle == "csv-v1" else self.bundle)

    async def list_datasets(self) -> tuple[str | None, list]:
        return self.config_id, []


@pytest.mark.asyncio
async def test_refetches_train_series_when_config_id_changes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)
        client = FakeClient()
        first = HistoricStore(client=client, cache_dir=cache_dir, refresh=False, ttl_ms=0)
        loaded = await first.get_train("mexico")
        assert len(loaded.slots) == 1
        assert client.train_fetches == 1

        cached = HistoricStore(client=client, cache_dir=cache_dir, refresh=False, ttl_ms=0)
        await cached.get_train("mexico")
        assert client.train_fetches == 1

        client.config_id = "level-b"
        nxt = HistoricStore(client=client, cache_dir=cache_dir, refresh=False, ttl_ms=0)
        await nxt.get_train("mexico")
        assert client.train_fetches == 2


@pytest.mark.asyncio
async def test_refetches_train_series_when_csv_bundle_hash_changes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)
        client = FakeClient()
        first = HistoricStore(client=client, cache_dir=cache_dir, refresh=False, ttl_ms=0)
        await first.get_train("mexico")
        assert client.train_fetches == 1

        cached = HistoricStore(client=client, cache_dir=cache_dir, refresh=False, ttl_ms=0)
        await cached.get_train("mexico")
        assert client.train_fetches == 1

        client.bundle = "csv-v2"
        nxt = HistoricStore(client=client, cache_dir=cache_dir, refresh=False, ttl_ms=0)
        await nxt.get_train("mexico")
        assert client.train_fetches == 2
