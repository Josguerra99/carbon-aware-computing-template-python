from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .math_helper import MathHelper

if TYPE_CHECKING:
    from .types import GhiSlot

FEATURE_COUNT = 28


@dataclass(frozen=True)
class TfTrainingConfig:
    max_samples: int = 120_000
    epochs: int = 12
    batch_size: int = 2048
    learning_rate: float = 1e-3
    validation_split: float = 0.05
    seed: int = 42


default_tf_training_config = TfTrainingConfig()


def _solar_hour_one_hot(timestamp: datetime, longitude: float) -> list[float]:
    hour = int(MathHelper.solar_hour(timestamp, longitude)) % 24
    flags = [0.0] * 24
    flags[hour] = 1.0
    return flags


def feature_vector(timestamp: datetime, latitude: float, longitude: float) -> list[float]:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return [
        *_solar_hour_one_hot(timestamp, longitude),
        float(MathHelper.day_of_year_utc(timestamp)),
        latitude,
        longitude,
        float(timestamp.astimezone(timezone.utc).year),
    ]


def _mulberry32(seed: int):
    """Deterministic shuffle (matches TypeScript tfCommon mulberry32)."""
    state = seed & 0xFFFFFFFF

    def rng() -> float:
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((state ^ (state >> 15)) * (1 | state)) & 0xFFFFFFFF
        t = (t + ((t ^ (t >> 7)) * (61 | t))) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rng


def _sample_rows(rows: list[Any], max_samples: int, seed: int) -> list[Any]:
    if len(rows) <= max_samples:
        return rows
    rng = _mulberry32(seed)
    indices = list(range(len(rows)))
    for i in range(len(indices) - 1, 0, -1):
        j = int(rng() * (i + 1))
        indices[i], indices[j] = indices[j], indices[i]
    return [rows[i] for i in indices[:max_samples]]


def build_training_arrays(
    training_data: list[GhiSlot],
    config: TfTrainingConfig | None = None,
) -> tuple[list[list[float]], list[float]]:
    cfg = config or default_tf_training_config
    if not training_data:
        return [], []
    rows = _sample_rows(training_data, cfg.max_samples, cfg.seed)
    xs = [feature_vector(slot.time, slot.latitude, slot.longitude) for slot in rows]
    ys = [max(0.0, slot.ghi_wm2) for slot in rows]
    return xs, ys


def train_keras_regressor(model: Any, training_data: list[GhiSlot], config: TfTrainingConfig | None = None) -> None:
    from .tf_backend import ensure_tf_backend

    ensure_tf_backend()
    cfg = config or default_tf_training_config
    xs, ys = build_training_arrays(training_data, cfg)
    if not xs:
        raise ValueError("No hay datos de entrenamiento")

    import numpy as np
    import tensorflow as tf

    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=cfg.learning_rate), loss="mse")
    x_arr = np.array(xs, dtype=np.float32)
    y_arr = np.array(ys, dtype=np.float32).reshape(-1, 1)
    model.fit(
        x_arr,
        y_arr,
        epochs=cfg.epochs,
        batch_size=cfg.batch_size,
        validation_split=cfg.validation_split,
        verbose=0,
    )


def predict_non_negative(model: Any, timestamp: datetime, latitude: float, longitude: float) -> float:
    values = predict_batch_non_negative(model, [timestamp], latitude, longitude)
    return values[0] if values else 0.0


def predict_batch_non_negative(
    model: Any,
    timestamps: list[datetime],
    latitude: float,
    longitude: float,
) -> list[float]:
    if not timestamps:
        return []
    from .tf_backend import ensure_tf_backend

    ensure_tf_backend()
    import numpy as np

    xs = np.array(
        [feature_vector(t, latitude, longitude) for t in timestamps],
        dtype=np.float32,
    )
    preds = model.predict(xs, verbose=0)
    flat = preds.reshape(-1)
    return [max(0.0, float(v)) for v in flat]
