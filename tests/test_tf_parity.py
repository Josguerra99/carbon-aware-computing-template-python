from __future__ import annotations

from datetime import datetime, timezone

from src.core.math_helper import MathHelper
from src.core.tf_common import FEATURE_COUNT, feature_vector
from src.core.tf_enhanced_common import ENHANCED_FEATURE_COUNT, enhanced_feature_vector

# Golden values from the same formulas in carbon-aware-computing-template (tfCommon / tfEnhancedCommon).
_GOLDEN_TS = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
_LAT = 14.63
_LON = -90.51


def test_enhanced_feature_vector_matches_typescript() -> None:
    v = enhanced_feature_vector(_GOLDEN_TS, _LAT, _LON)
    assert len(v) == ENHANCED_FEATURE_COUNT
    assert v == [
        0.8660254037844387,
        -0.4999999999999998,
        0.26556302780405594,
        -0.9640935007889755,
        0.16255555555555556,
        -0.5028333333333334,
        1.9889604166666668,
    ]


def test_base_feature_vector_solar_hour_and_doy() -> None:
    v = feature_vector(_GOLDEN_TS, _LAT, _LON)
    assert len(v) == FEATURE_COUNT
    assert v.index(1.0) == 8
    assert v[24] == float(MathHelper.day_of_year_utc(_GOLDEN_TS))
    assert v[25] == _LAT
    assert v[26] == _LON
    assert v[27] == 2024.0


def test_mulberry32_sample_matches_typescript_seed_order() -> None:
    from src.core.tf_common import _sample_rows

    rows = list(range(100))
    a = _sample_rows(rows, 40, 42)
    b = _sample_rows(rows, 40, 42)
    assert a == b
    assert len(a) == 40
    assert sorted(a) != a
