from __future__ import annotations

import math
import random
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .math_helper import MathHelper
from .tf_common import TfTrainingConfig, _sample_rows


def _day_of_year_utc(timestamp: datetime) -> int:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    utc = timestamp.astimezone(timezone.utc)
    start = datetime(utc.year, 1, 1, tzinfo=timezone.utc)
    day = datetime(utc.year, utc.month, utc.day, tzinfo=timezone.utc)
    return int((day - start).total_seconds() // 86_400) + 1

if TYPE_CHECKING:
    from .types import GhiSlot

ENHANCED_FEATURE_COUNT = 7

default_enhanced_tf_training_config = TfTrainingConfig(
    max_samples=120_000,
    epochs=12,
    batch_size=4096,
    learning_rate=1e-3,
    validation_split=0.05,
    seed=42,
)


def enhanced_feature_vector(timestamp: datetime, latitude: float, longitude: float) -> list[float]:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    hour = MathHelper.solar_hour(timestamp, longitude)
    solar_angle = (2 * math.pi * hour) / 24
    doy = _day_of_year_utc(timestamp)
    doy_angle = (2 * math.pi * doy) / 365.25
    unix_days = timestamp.astimezone(timezone.utc).timestamp() / 86_400
    return [
        math.sin(solar_angle),
        math.cos(solar_angle),
        math.sin(doy_angle),
        math.cos(doy_angle),
        latitude / 90,
        longitude / 180,
        unix_days / 10_000,
    ]


def build_enhanced_training_arrays(
    training_data: list[GhiSlot],
    config: TfTrainingConfig | None = None,
) -> tuple[list[list[float]], list[float]]:
    cfg = config or default_enhanced_tf_training_config
    if not training_data:
        return [], []
    rows = _sample_rows(training_data, cfg.max_samples, cfg.seed)
    xs = [enhanced_feature_vector(slot.time, slot.latitude, slot.longitude) for slot in rows]
    ys = [max(0.0, slot.ghi_wm2) for slot in rows]
    return xs, ys


def train_enhanced_keras_regressor(
    model: Any,
    training_data: list[GhiSlot],
    config: TfTrainingConfig | None = None,
) -> None:
    from .tf_backend import ensure_tf_backend

    ensure_tf_backend()
    cfg = config or default_enhanced_tf_training_config
    xs, ys = build_enhanced_training_arrays(training_data, cfg)
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


def predict_enhanced_non_negative(
    model: Any,
    timestamp: datetime,
    latitude: float,
    longitude: float,
) -> float:
    values = predict_enhanced_batch_non_negative(model, [timestamp], latitude, longitude)
    return values[0] if values else 0.0


def predict_enhanced_batch_non_negative(
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
        [enhanced_feature_vector(t, latitude, longitude) for t in timestamps],
        dtype=np.float32,
    )
    preds = model.predict(xs, verbose=0)
    flat = preds.reshape(-1)
    return [max(0.0, float(v)) for v in flat]
