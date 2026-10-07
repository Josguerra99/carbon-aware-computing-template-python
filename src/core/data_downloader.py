from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .types import GhiHistoric, GhiSlot, HistoricDatasetInfo

MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL", "http://192.168.0.232:3915").rstrip("/")
CACHE_DIR = Path(__file__).resolve().parents[2] / "cache"
_MEM: dict[str, GhiHistoric] = {}


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _to_slots(payload: dict) -> list[GhiSlot]:
    dataset_id = payload.get("datasetId") or "unknown"
    latitude = float(payload.get("latitude") or 0)
    longitude = float(payload.get("longitude") or 0)
    slots: list[GhiSlot] = []
    for raw in payload.get("slots") or []:
        moment = _parse_time(raw.get("time") or raw.get("start"))
        if moment is None:
            continue
        slots.append(
            GhiSlot(
                dataset_id=dataset_id,
                time=moment,
                ghi_wm2=float(raw.get("ghiWm2") or 0),
                latitude=latitude,
                longitude=longitude,
                cloud_cover_pct=raw.get("cloudCoverPct"),
                temperature_c=raw.get("temperatureC"),
            )
        )
    return slots


def _to_historic(payload: dict) -> GhiHistoric:
    return GhiHistoric(
        dataset_id=payload.get("datasetId"),
        latitude=float(payload.get("latitude") or 0),
        longitude=float(payload.get("longitude") or 0),
        slots=_to_slots(payload),
    )


def _has_coords(payload: dict) -> bool:
    lat = payload.get("latitude")
    lon = payload.get("longitude")
    return isinstance(lat, (int, float)) and isinstance(lon, (int, float))


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def list_historic_datasets(client: httpx.Client | None = None) -> list[HistoricDatasetInfo]:
    url = f"{MAIN_SERVER_URL}/api/historic/ghi"
    if client is None:
        with httpx.Client(timeout=30.0) as own:
            response = own.get(url)
    else:
        response = client.get(url)
    response.raise_for_status()
    payload = response.json()
    datasets = payload.get("datasets") or []
    result: list[HistoricDatasetInfo] = []
    for item in datasets:
        if not isinstance(item, dict):
            continue
        dataset_id = item.get("id")
        if not isinstance(dataset_id, str) or not dataset_id:
            continue
        result.append(
            HistoricDatasetInfo(
                id=dataset_id,
                name=str(item.get("name") or dataset_id),
                city=str(item.get("city") or ""),
                country=str(item.get("country") or ""),
                latitude=float(item.get("latitude") or 0),
                longitude=float(item.get("longitude") or 0),
                timezone=str(item.get("timezone") or "UTC"),
                kind=item.get("kind") if item.get("kind") in ("department", "country") else "department",
            )
        )
    return result


def load_historic(dataset_id: str, client: httpx.Client | None = None) -> GhiHistoric:
    cached_mem = _MEM.get(dataset_id)
    if cached_mem is not None:
        return cached_mem

    path = CACHE_DIR / f"{dataset_id}.json"
    cached = _read_json(path)
    if cached is not None and _has_coords(cached):
        historic = _to_historic(cached)
        _MEM[dataset_id] = historic
        return historic

    url = f"{MAIN_SERVER_URL}/api/historic/ghi/{dataset_id}"
    if client is None:
        with httpx.Client(timeout=60.0) as own:
            response = own.get(url)
    else:
        response = client.get(url)
    response.raise_for_status()
    payload = response.json()
    if not _has_coords(payload):
        raise ValueError(f"El histórico de {dataset_id} no trae latitude/longitude")
    _write_json(path, payload)
    historic = _to_historic(payload)
    _MEM[dataset_id] = historic
    return historic
