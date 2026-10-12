from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

from src.config.env import HISTORIC_CACHE_TTL_MS, REFRESH_HISTORIC
from src.core.cache_bundle import cache_bundle_matches, manifest_cache_stale
from src.core.types import GhiHistoric, GhiSeriesJson, GhiSlot, HistoricDatasetInfo
from src.core.workshop_client import DatasetMeta, WorkshopClient, WorkshopManifest, create_workshop_client


class DiskEnvelope(TypedDict, total=False):
    configId: str
    csvBundleHash: str
    csvFingerprint: str
    fetchedAt: float
    payload: Any


@dataclass
class MemEntry:
    config_id: str
    csv_bundle_hash: str | None = None
    meta: DatasetMeta | None = None
    meta_fetched_at: float | None = None
    train: GhiHistoric | None = None
    train_fetched_at: float | None = None


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _to_date_slots(historic: GhiSeriesJson) -> list[GhiSlot]:
    dataset_id = historic.get("datasetId") or "unknown"
    latitude = historic.get("latitude") or 0.0
    longitude = historic.get("longitude") or 0.0
    slots: list[GhiSlot] = []
    for slot in historic.get("slots") or []:
        raw_time = slot.get("time") or slot.get("start") or ""
        time = _parse_iso(raw_time)
        if time is None:
            continue
        slots.append(
            GhiSlot(
                dataset_id=dataset_id,
                time=time,
                ghi_wm2=float(slot.get("ghiWm2") or 0),
                latitude=latitude,
                longitude=longitude,
                cloud_cover_pct=slot.get("cloudCoverPct"),
                temperature_c=slot.get("temperatureC"),
            )
        )
    return slots


def _to_historic(payload: GhiSeriesJson) -> GhiHistoric:
    return GhiHistoric(
        dataset_id=payload.get("datasetId"),
        latitude=float(payload.get("latitude") or 0),
        longitude=float(payload.get("longitude") or 0),
        slots=_to_date_slots(payload),
    )


def _has_coords(payload: dict[str, Any]) -> bool:
    lat = payload.get("latitude")
    lon = payload.get("longitude")
    return isinstance(lat, (int, float)) and isinstance(lon, (int, float))


def _fresh(fetched_at: float | None, ttl_ms: int) -> bool:
    if fetched_at is None:
        return False
    if ttl_ms <= 0:
        return True
    return (time.time() * 1000) - fetched_at < ttl_ms


@dataclass
class HistoricStore:
    client: WorkshopClient
    cache_dir: Path
    ttl_ms: int = HISTORIC_CACHE_TTL_MS
    refresh: bool = REFRESH_HISTORIC
    _mem: dict[str, MemEntry] = field(default_factory=dict)
    _manifest: WorkshopManifest | None = None

    async def _read_json_file(self, path: Path) -> Any | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except OSError:
            return None
        except json.JSONDecodeError:
            return None

    async def _write_json_file(self, path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    async def _clear_disk(self) -> None:
        for sub in ("meta", "train"):
            target = self.cache_dir / sub
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)

    async def _ensure_manifest(self) -> WorkshopManifest:
        if self._manifest is not None:
            return self._manifest
        remote = await self.client.fetch_manifest()
        disk_path = self.cache_dir / "manifest.json"
        disk = None if self.refresh else await self._read_json_file(disk_path)
        if manifest_cache_stale(disk, remote):
            self._mem.clear()
            await self._clear_disk()
        if self.refresh:
            self._mem.clear()
        self._manifest = remote
        await self._write_json_file(disk_path, remote)
        return remote

    def _entry(self, dataset_id: str, config_id: str, csv_bundle_hash: str | None) -> MemEntry:
        current = self._mem.get(dataset_id)
        if (
            current is not None
            and current.config_id == config_id
            and (csv_bundle_hash is None or current.csv_bundle_hash == csv_bundle_hash)
        ):
            return current
        next_entry = MemEntry(config_id=config_id, csv_bundle_hash=csv_bundle_hash)
        self._mem[dataset_id] = next_entry
        return next_entry

    async def get_meta(self, dataset_id: str) -> DatasetMeta:
        current = await self._ensure_manifest()
        config_id = current["configId"]
        csv_hash = current.get("csvBundleHash")
        cached = self._mem.get(dataset_id)
        if (
            cached
            and cached.config_id == config_id
            and cached.csv_bundle_hash == csv_hash
            and cached.meta
            and _has_coords(cached.meta)
            and _fresh(cached.meta_fetched_at, self.ttl_ms)
        ):
            return cached.meta
        if not self.refresh:
            disk = await self._read_json_file(self.cache_dir / "meta" / f"{dataset_id}.json")
            if (
                isinstance(disk, dict)
                and cache_bundle_matches(disk, current)
                and isinstance(disk.get("payload"), dict)
                and _has_coords(disk["payload"])
                and _fresh(disk.get("fetchedAt"), self.ttl_ms)
            ):
                payload = disk["payload"]
                row = self._entry(dataset_id, config_id, csv_hash)
                row.meta = payload  # type: ignore[assignment]
                row.meta_fetched_at = float(disk["fetchedAt"])
                return payload  # type: ignore[return-value]
        payload = await self.client.fetch_meta(dataset_id)
        if not _has_coords(payload):
            raise RuntimeError(f"El meta de {dataset_id} no trae latitude/longitude")
        fetched_at = time.time() * 1000
        row = self._entry(dataset_id, config_id, csv_hash)
        row.meta = payload
        row.meta_fetched_at = fetched_at
        await self._write_json_file(
            self.cache_dir / "meta" / f"{dataset_id}.json",
            {
                "configId": config_id,
                "csvBundleHash": csv_hash,
                "csvFingerprint": payload.get("csvFingerprint"),
                "fetchedAt": fetched_at,
                "payload": payload,
            },
        )
        return payload

    async def get_train(self, dataset_id: str) -> GhiHistoric:
        current = await self._ensure_manifest()
        config_id = current["configId"]
        csv_hash = current.get("csvBundleHash")
        cached = self._mem.get(dataset_id)
        if (
            cached
            and cached.config_id == config_id
            and cached.csv_bundle_hash == csv_hash
            and cached.train
            and _fresh(cached.train_fetched_at, self.ttl_ms)
        ):
            return cached.train
        if not self.refresh:
            disk = await self._read_json_file(self.cache_dir / "train" / f"{dataset_id}.json")
            if (
                isinstance(disk, dict)
                and cache_bundle_matches(disk, current)
                and isinstance(disk.get("payload"), dict)
                and _has_coords(disk["payload"])
                and isinstance(disk["payload"].get("slots"), list)
                and _fresh(disk.get("fetchedAt"), self.ttl_ms)
            ):
                historic = _to_historic(disk["payload"])
                row = self._entry(dataset_id, config_id, csv_hash)
                row.train = historic
                row.train_fetched_at = float(disk["fetchedAt"])
                if row.meta is None:
                    row.meta = {
                        "datasetId": historic.dataset_id or dataset_id,
                        "latitude": historic.latitude,
                        "longitude": historic.longitude,
                    }
                    row.meta_fetched_at = float(disk["fetchedAt"])
                return historic
        payload = await self.client.fetch_train_series(dataset_id)
        if not _has_coords(payload):
            raise RuntimeError(f"El histórico de {dataset_id} no trae latitude/longitude")
        historic = _to_historic(payload)
        fetched_at = time.time() * 1000
        row = self._entry(dataset_id, config_id, csv_hash)
        row.train = historic
        row.train_fetched_at = fetched_at
        row.meta = {
            "configId": config_id,
            "datasetId": historic.dataset_id or dataset_id,
            "latitude": historic.latitude,
            "longitude": historic.longitude,
            "csvFingerprint": payload.get("csvFingerprint"),
        }
        row.meta_fetched_at = fetched_at
        await self._write_json_file(
            self.cache_dir / "train" / f"{dataset_id}.json",
            {
                "configId": config_id,
                "csvBundleHash": csv_hash,
                "csvFingerprint": payload.get("csvFingerprint"),
                "fetchedAt": fetched_at,
                "payload": payload,
            },
        )
        return historic

    async def list_datasets(self) -> list[HistoricDatasetInfo]:
        await self._ensure_manifest()
        _config_id, datasets = await self.client.list_datasets()
        return datasets


def create_historic_store(
    client: WorkshopClient | None = None,
    cache_dir: Path | None = None,
    ttl_ms: int | None = None,
    refresh: bool | None = None,
) -> HistoricStore:
    root = Path(__file__).resolve().parents[2]
    return HistoricStore(
        client=client or create_workshop_client(),
        cache_dir=cache_dir or (root / "cache"),
        ttl_ms=HISTORIC_CACHE_TTL_MS if ttl_ms is None else ttl_ms,
        refresh=REFRESH_HISTORIC if refresh is None else refresh,
    )


historic_store = create_historic_store()
