from __future__ import annotations

from typing import TypedDict

from src.core.workshop_client import WorkshopManifest


class CachedBundle(TypedDict, total=False):
    configId: str
    csvBundleHash: str


def cache_bundle_matches(disk: CachedBundle | None, remote: WorkshopManifest) -> bool:
    if not disk or disk.get("configId") != remote.get("configId"):
        return False
    remote_hash = remote.get("csvBundleHash")
    if remote_hash is not None and disk.get("csvBundleHash") != remote_hash:
        return False
    return True


def manifest_cache_stale(disk: CachedBundle | None, remote: WorkshopManifest) -> bool:
    return disk is not None and not cache_bundle_matches(disk, remote)
