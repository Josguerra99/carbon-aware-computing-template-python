from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from src.config.env import TRAIN_DATASETS
from src.core.historic_store import historic_store
from src.core.types import GhiSlot

TRAIN_CONCURRENCY = 4


def _dataset_filter() -> set[str] | None:
    raw = TRAIN_DATASETS
    if not raw or raw.lower() in ("all", "*"):
        return None
    ids = [part.strip() for part in raw.split(",") if part.strip()]
    return set(ids) if ids else None


async def map_pool[T, R](
    items: list[T],
    concurrency: int,
    fn: Callable[[T], Awaitable[R]],
) -> list[R]:
    results: list[R | None] = [None] * len(items)
    index = 0
    lock = asyncio.Lock()

    async def worker() -> None:
        nonlocal index
        while True:
            async with lock:
                if index >= len(items):
                    return
                current = index
                index += 1
            results[current] = await fn(items[current])

    workers = min(concurrency, len(items)) if items else 0
    await asyncio.gather(*(worker() for _ in range(workers)))
    return [results[i] for i in range(len(items))]  # type: ignore[misc]


class LoadTrainingData:
    @staticmethod
    async def load() -> list[GhiSlot]:
        allowed = _dataset_filter()
        datasets = await historic_store.list_datasets()
        selected = [d for d in datasets if allowed is None or d.get("id") in allowed]
        if not selected:
            raise RuntimeError("No hay datasets de entrenamiento (revisa TRAIN_DATASETS)")

        async def load_one(dataset: dict) -> list[GhiSlot]:
            dataset_id = dataset["id"]
            historic = await historic_store.get_train(dataset_id)
            return historic.slots

        loaded = await map_pool(selected, TRAIN_CONCURRENCY, load_one)
        flat: list[GhiSlot] = []
        for chunk in loaded:
            flat.extend(chunk)
        return flat
