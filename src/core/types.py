from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypedDict


class GhiSlotJson(TypedDict, total=False):
    time: str
    start: str
    ghiWm2: float
    cloudCoverPct: float | None
    temperatureC: float | None


class GhiSeriesJson(TypedDict, total=False):
    datasetId: str
    location: str
    latitude: float
    longitude: float
    unit: str
    source: str
    slots: list[GhiSlotJson]
    csvFingerprint: str


class HistoricDatasetInfo(TypedDict, total=False):
    id: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    timezone: str
    kind: Literal["department", "country"]


@dataclass
class GhiSlot:
    dataset_id: str
    time: datetime
    ghi_wm2: float
    latitude: float
    longitude: float
    cloud_cover_pct: float | None
    temperature_c: float | None


@dataclass
class GhiHistoric:
    latitude: float
    longitude: float
    slots: list[GhiSlot]
    dataset_id: str | None = None


class ForecastPoint(TypedDict):
    time: str
    predWm2: float
