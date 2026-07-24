# tests/unit/test_features.py
import pandas as pd
from feature_engineering.features import (
    add_lag_features,
    add_time_features,
    remove_initial_nan_rows,
)


def make_df():
    dates = pd.date_range("2020-01-01", periods=15, freq="MS")
    return pd.DataFrame(
        {"date": dates, "country": "Nepal", "month": dates.month, "arrivals": range(15)}
    )


def test_month_sin_cos_bounded():
    df = add_time_features(make_df())
    assert df["month_sin"].between(-1, 1).all()


def test_lag_1_shifts_correctly():
    df = add_lag_features(make_df())
    assert df["lag_1"].iloc[1] == df["arrivals"].iloc[0]


def test_remove_initial_nan_rows_drops_leading_rows():
    df = add_lag_features(make_df())  # lag_12 needs 12 prior rows
    cleaned = remove_initial_nan_rows(df)
    assert cleaned["lag_12"].isna().sum() == 0
