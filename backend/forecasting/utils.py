from __future__ import annotations
import numpy as np
import pandas as pd
from feature_engineering.constants import (
    LAG_MONTHS,
    ROLLING_WINDOWS,
    MONTHS_IN_YEAR,
    SPRING_MONTHS,
    AUTUMN_MONTHS,
    MONSOON_MONTHS,
    COVID_START,
    COVID_END,
)


def next_month(date: pd.Timestamp) -> pd.Timestamp:
    return date + pd.offsets.MonthBegin(1)


def update_lag_features(history: list[float]) -> dict[str, float]:
    features = {}
    for lag in LAG_MONTHS:
        if len(history) >= lag:
            features[f"lag_{lag}"] = history[-lag]
        else:
            features[f"lag_{lag}"] = np.nan
    return features


def update_rolling_features(history: list[float]) -> dict[str, float]:
    features = {}
    for window in ROLLING_WINDOWS:
        values = history[-window:]
        if len(values) == 0:
            mean = np.nan
            std = np.nan
        else:
            mean = float(np.mean(values))
            std = float(np.std(values))
        features[f"rolling_mean_{window}"] = mean
        features[f"rolling_std_{window}"] = std
    return features


def update_time_features(date: pd.Timestamp, time_index: int) -> dict[str, float]:
    month = date.month
    angle = 2 * np.pi * (month - 1) / MONTHS_IN_YEAR
    return {
        "month": month,
        "month_sin": np.sin(angle),
        "month_cos": np.cos(angle),
        "time_index": time_index,
    }


def update_season_flags(date: pd.Timestamp) -> dict[str, int]:
    month = date.month
    current = date.strftime("%Y-%m-%d")
    return {
        "is_spring_trek": int(month in SPRING_MONTHS),
        "is_autumn_trek": int(month in AUTUMN_MONTHS),
        "is_monsoon": int(month in MONSOON_MONTHS),
        "is_covid": int(COVID_START <= current <= COVID_END),
    }
