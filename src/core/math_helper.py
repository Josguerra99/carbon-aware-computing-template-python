from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone


def create_parabola(height: float, start: float, end: float) -> Callable[[float], float]:
    mid = (start + end) / 2
    half = (end - start) / 2

    def parabola(x: float) -> float:
        return height * (1 - ((x - mid) / half) ** 2)

    return parabola


def create_linear_regression(points: list[tuple[float, float]]) -> Callable[[float], float]:
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_xx = sum(p[0] * p[0] for p in points)
    n = len(points)
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return lambda _x: sum_y / n if n else 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return lambda x: intercept + slope * x


def solar_hour(timestamp: datetime, longitude: float) -> int:
    ts = timestamp.astimezone(timezone.utc) if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    utc = ts.hour + ts.minute / 60 + ts.second / 3600
    hour = (utc + longitude / 15) % 24
    return int(round((hour + 24) % 24))
