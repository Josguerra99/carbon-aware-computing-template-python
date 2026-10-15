from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.core.types import GhiSlot
from src.workshop.helios_clear_sky import HeliosClearSky
from src.workshop.solar_geometry import clear_sky_hour_mean, cos_solar_zenith

LAT = 14.6
LON = -90.5


def _slot(ms: float, ghi: float) -> GhiSlot:
    return GhiSlot(
        dataset_id="test",
        time=datetime.fromtimestamp(ms / 1000, tz=timezone.utc),
        ghi_wm2=ghi,
        latitude=LAT,
        longitude=LON,
        cloud_cover_pct=None,
        temperature_c=None,
    )


def test_solar_geometry_noon_and_night() -> None:
    noon = datetime(2024, 6, 1, 18, 0, tzinfo=timezone.utc).timestamp() * 1000
    night = datetime(2024, 6, 1, 6, 0, tzinfo=timezone.utc).timestamp() * 1000
    assert cos_solar_zenith(noon, LAT, LON) > 0.9
    assert cos_solar_zenith(night, LAT, LON) < 0
    assert clear_sky_hour_mean(night, LAT, LON) == 0


@pytest.mark.asyncio
async def test_helios_clear_sky_constant_ratio() -> None:
    rows: list[GhiSlot] = []
    start = datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp() * 1000
    end = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000
    ms = start
    while ms < end:
        cs = clear_sky_hour_mean(ms, LAT, LON)
        rows.append(_slot(ms, 0.7 * cs))
        ms += 3_600_000
    model = HeliosClearSky()
    await model.train(rows)
    noon = datetime(2024, 3, 10, 18, 0, tzinfo=timezone.utc)
    pred = await model.forecast(noon, LAT, LON)
    expected = 0.7 * clear_sky_hour_mean(noon.timestamp() * 1000, LAT, LON)
    assert pred == pytest.approx(expected, rel=0, abs=1.0)
    night = datetime(2024, 3, 10, 6, 0, tzinfo=timezone.utc)
    assert await model.forecast(night, LAT, LON) == 0


@pytest.mark.asyncio
async def test_helios_clear_sky_nearest_site() -> None:
    model = HeliosClearSky()
    ms = datetime(2023, 6, 1, 18, 0, tzinfo=timezone.utc).timestamp() * 1000
    await model.train([_slot(ms, 800)])
    pred = await model.forecast(datetime(2024, 6, 1, 18, 0, tzinfo=timezone.utc), LAT + 0.5, LON)
    assert pred > 0
