from __future__ import annotations

from typing import Protocol, TypedDict
from urllib.parse import quote

import httpx

from src.config.env import MAIN_SERVER_URL
from src.core.types import GhiSeriesJson, HistoricDatasetInfo


class WorkshopManifest(TypedDict, total=False):
    configId: str
    configName: str
    scenarioCount: int
    datasetsHash: str
    csvBundleHash: str
    generatedAt: str


class DatasetMeta(TypedDict, total=False):
    configId: str
    datasetId: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    timezone: str
    kind: str
    csvFingerprint: str


class WorkshopClient(Protocol):
    async def fetch_manifest(self) -> WorkshopManifest: ...
    async def fetch_meta(self, dataset_id: str) -> DatasetMeta: ...
    async def fetch_train_series(self, dataset_id: str) -> GhiSeriesJson: ...
    async def list_datasets(self) -> tuple[str | None, list[HistoricDatasetInfo]]: ...


async def _read_json(client: httpx.AsyncClient, url: str) -> object:
    response = await client.get(url)
    if response.status_code >= 400:
        raise RuntimeError(f"No se pudo leer {url} (HTTP {response.status_code})")
    return response.json()


def create_workshop_client(base_url: str = MAIN_SERVER_URL) -> WorkshopClient:
    main = base_url.rstrip("/")

    class _Client:
        def __init__(self) -> None:
            self._http = httpx.AsyncClient(timeout=60.0)

        async def fetch_manifest(self) -> WorkshopManifest:
            payload = await _read_json(self._http, f"{main}/api/workshop/manifest")
            return payload  # type: ignore[return-value]

        async def fetch_meta(self, dataset_id: str) -> DatasetMeta:
            payload = await _read_json(
                self._http,
                f"{main}/api/workshop/datasets/{quote(dataset_id, safe='')}/meta",
            )
            return payload  # type: ignore[return-value]

        async def fetch_train_series(self, dataset_id: str) -> GhiSeriesJson:
            payload = await _read_json(
                self._http,
                f"{main}/api/historic/ghi/{quote(dataset_id, safe='')}/train",
            )
            return payload  # type: ignore[return-value]

        async def list_datasets(self) -> tuple[str | None, list[HistoricDatasetInfo]]:
            payload = await _read_json(self._http, f"{main}/api/historic/ghi")
            if not isinstance(payload, dict):
                return None, []
            config_id = payload.get("configId")
            datasets_raw = payload.get("datasets")
            datasets: list[HistoricDatasetInfo] = []
            if isinstance(datasets_raw, list):
                for item in datasets_raw:
                    if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]:
                        datasets.append(item)  # type: ignore[arg-type]
            return (config_id if isinstance(config_id, str) else None, datasets)

    return _Client()
