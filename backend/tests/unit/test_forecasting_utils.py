# tests/unit/test_forecasting_utils.py
import pandas as pd
from forecasting.utils import next_month, update_lag_features


def test_next_month_rolls_year():
    assert next_month(pd.Timestamp("2025-12-01")) == pd.Timestamp("2026-01-01")


def test_update_lag_features_short_history_gives_nan():
    feats = update_lag_features([100.0])  # lag_12 impossible with 1 data point
    import math

    assert math.isnan(feats["lag_12"])
