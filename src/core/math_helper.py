from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Callable


class MathHelper:
    @staticmethod
    def day_of_year_utc(timestamp: datetime) -> int:
        """Same numbering as TypeScript MathHelper.dayOfYearUtc / tfCommon dayOfYearUtc."""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        utc = timestamp.astimezone(timezone.utc)
        year = utc.year
        start = datetime(year - 1, 12, 31, tzinfo=timezone.utc)
        day = datetime(year, utc.month, utc.day, tzinfo=timezone.utc)
        return int((day - start).total_seconds() // 86_400)

    @staticmethod
    def _solve_system(matrix: list[list[float]], vector: list[float]) -> list[float] | None:
        n = len(matrix)
        rows = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
        for col in range(n):
            pivot = col
            for row in range(col + 1, n):
                if abs(rows[row][col]) > abs(rows[pivot][col]):
                    pivot = row
            rows[col], rows[pivot] = rows[pivot], rows[col]
            diag = rows[col][col]
            if abs(diag) < 1e-12:
                return None
            for j in range(col, n + 1):
                rows[col][j] /= diag
            for row in range(n):
                if row == col:
                    continue
                factor = rows[row][col]
                for j in range(col, n + 1):
                    rows[row][j] -= factor * rows[col][j]
        return [row[n] for row in rows]

    @staticmethod
    def fit_by_features(
        samples: list[list[float]],
        y: list[float],
    ) -> Callable[[list[float]], float] | None:
        n = len(samples)
        k = len(samples[0]) if samples else 0
        if n < k or k == 0:
            return None
        ata = [[0.0] * k for _ in range(k)]
        aty = [0.0] * k
        for i in range(n):
            row = samples[i]
            target = y[i]
            for a in range(k):
                aty[a] += row[a] * target
                for b in range(k):
                    ata[a][b] += row[a] * row[b]
        weights = MathHelper._solve_system(ata, aty)
        if weights is None:
            return None
        return lambda features: sum(w * features[i] for i, w in enumerate(weights))

    @staticmethod
    def sine_features(doy: float) -> list[float]:
        angle = (2 * math.pi * (doy - 1)) / 365.25
        return [1.0, math.sin(angle), math.cos(angle)]

    @staticmethod
    def _plus_cube(value: float, knot: float) -> float:
        delta = value - knot
        return delta**3 if delta > 0 else 0.0

    @staticmethod
    def poly_spline_features(xn: float) -> list[float]:
        return [
            1.0,
            xn,
            xn * xn,
            xn**3,
            MathHelper._plus_cube(xn, 0.2),
            MathHelper._plus_cube(xn, 0.4),
            MathHelper._plus_cube(xn, 0.6),
            MathHelper._plus_cube(xn, 0.8),
        ]

    @staticmethod
    def sine_features_from_time_ms(t_ms: float, t_min: float, t_max: float) -> list[float]:
        xn = (t_ms - t_min) / (t_max - t_min or 1)
        angle = 2 * math.pi * xn
        return [1.0, math.sin(angle), math.cos(angle)]

    @staticmethod
    def create_sine_cosine_regression(
        points: list[dict[str, float]],
    ) -> Callable[[float], float] | None:
        if len(points) < 3:
            return None
        predict = MathHelper.fit_by_features(
            [MathHelper.sine_features(p["doy"]) for p in points],
            [p["y"] for p in points],
        )
        if predict is None:
            return None
        return lambda doy: predict(MathHelper.sine_features(doy))

    @staticmethod
    def create_sine_cosine_regression_on_time_ms(
        points: list[dict[str, float]],
    ) -> Callable[[float], float] | None:
        if len(points) < 3:
            return None
        t_min = min(p["x"] for p in points)
        t_max = max(p["x"] for p in points)

        def features_at(t_ms: float) -> list[float]:
            return MathHelper.sine_features_from_time_ms(t_ms, t_min, t_max)

        predict = MathHelper.fit_by_features(
            [features_at(p["x"]) for p in points],
            [p["y"] for p in points],
        )
        if predict is None:
            return None
        return lambda t_ms: predict(features_at(t_ms))

    @staticmethod
    def create_polynomial_spline_regression(
        points: list[dict[str, float]],
    ) -> Callable[[float], float] | None:
        if len(points) < 8:
            return None
        min_x = min(p["x"] for p in points)
        max_x = max(p["x"] for p in points)
        span = max_x - min_x or 1
        predict = MathHelper.fit_by_features(
            [MathHelper.poly_spline_features((p["x"] - min_x) / span) for p in points],
            [p["y"] for p in points],
        )
        if predict is None:
            return None
        return lambda x: predict(MathHelper.poly_spline_features((x - min_x) / span))

    @staticmethod
    def create_parabola(height: float, start: float, end: float) -> Callable[[float], float]:
        mid = (start + end) / 2
        half = (end - start) / 2

        def fn(x: float) -> float:
            return height * (1 - ((x - mid) / half) ** 2)

        return fn

    @staticmethod
    def create_linear_regression(points: list[dict[str, float]]) -> Callable[[float], float]:
        sum_x = sum(p["x"] for p in points)
        sum_y = sum(p["y"] for p in points)
        sum_xy = sum(p["x"] * p["y"] for p in points)
        sum_xx = sum(p["x"] * p["x"] for p in points)
        n = len(points)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        return lambda x: intercept + slope * x

    @staticmethod
    def solar_hour(timestamp: datetime, longitude: float) -> float:
        from datetime import timezone

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        utc_dt = timestamp.astimezone(timezone.utc)
        utc = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
        return round(((utc + longitude / 15) % 24 + 24) % 24) % 24
