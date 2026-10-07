from dataclasses import dataclass
from datetime import datetime
from typing import Literal


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
    dataset_id: str | None
    latitude: float
    longitude: float
    slots: list[GhiSlot]


@dataclass
class HistoricDatasetInfo:
    id: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    timezone: str
    kind: Literal["department", "country"]
