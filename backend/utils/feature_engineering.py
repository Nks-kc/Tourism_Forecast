"""
utils/feature_engineering.py
------------------------------
Transforms the clean monthly CSV into features the models can learn from.

WHY DO WE NEED FEATURES?
  The models don't understand "January" or "trekking season."
  We encode that knowledge as numbers so the models can use it.

FEATURES CREATED:
  ┌────────────────┬──────────────────────────────────────────────────────┐
  │ Feature        │ What it encodes                                      │
  ├────────────────┼──────────────────────────────────────────────────────┤
  │ month_sin/cos  │ Cyclical month (Dec and Jan are "close" numerically) │
  │ year_norm      │ Long-term growth trend (normalized 0–1)              │
  │ is_spring_trek │ 1 if Mar/Apr/May (peak spring trekking season)       │
  │ is_autumn_trek │ 1 if Sep/Oct/Nov (peak autumn trekking season)       │
  │ is_monsoon     │ 1 if Jun/Jul/Aug (low tourist season)                │
  │ is_covid       │ 1 if 2020–2021 (structural anomaly flag)             │
  │ lag_1          │ Tourist count last month                             │
  │ lag_3          │ Tourist count 3 months ago                           │
  │ lag_12         │ Tourist count same month last year (strongest signal)│
  └────────────────┴──────────────────────────────────────────────────────┘
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_CSV, FEATURE_COLS, TARGET_COL, TEST_MONTHS


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all features to the cleaned monthly dataframe.

    Args:
        df: DataFrame with columns [date, foreign_arrivals, year, month]

    Returns:
        DataFrame with all FEATURE_COLS added.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)

    # ── Cyclical month encoding ────────────────────────────────────────────────
    # PROBLEM: Month is a number 1–12. The model might think Dec (12) is far
    # from Jan (1), but they are adjacent months.
    # SOLUTION: Map months onto a circle using sin/cos.
    #   month_sin = sin(2π × month / 12)
    #   month_cos = cos(2π × month / 12)
    # Now Jan and Dec are very close in (sin, cos) space. ✓
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # ── Long-term growth trend ─────────────────────────────────────────────────
    # Nepal's tourism has grown significantly from the 1960s to today.
    # We give the model a normalized year value (0 = first year, 1 = last year)
    # so it can learn this growth pattern.
    year_min = df["year"].min()
    year_max = df["year"].max()
    denom    = max(year_max - year_min, 1)  # avoid division by zero
    df["year_norm"] = (df["year"] - year_min) / denom

    # ── Seasonal binary flags ──────────────────────────────────────────────────
    # These capture Nepal's unique tourism calendar patterns.

    # Spring trekking: Everest Base Camp, Annapurna circuit are busiest Mar–May
    df["is_spring_trek"] = df["month"].isin([3, 4, 5]).astype(int)

    # Autumn trekking: Sep–Nov is the most popular trekking season in Nepal
    df["is_autumn_trek"] = df["month"].isin([9, 10, 11]).astype(int)

    # Monsoon low season: heavy rain makes trekking difficult Jun–Aug
    df["is_monsoon"] = df["month"].isin([6, 7, 8]).astype(int)

    # ── COVID structural anomaly flag ─────────────────────────────────────────
    # 2020 and 2021 are NOT representative of normal tourism patterns.
    # We include them so the model learns the full history, but this flag
    # lets it "know" those years were abnormal — it should not generalize
    # that pattern into future predictions.
    df["is_covid"] = df["year"].isin([2020, 2021]).astype(int)

    # ── Lag features ──────────────────────────────────────────────────────────
    # "What were arrivals N months ago?"
    # These are among the most powerful features for time series forecasting
    # because tourism has strong autocorrelation (last month predicts this month).
    df["lag_1"]  = df[TARGET_COL].shift(1)    # last month
    df["lag_3"]  = df[TARGET_COL].shift(3)    # 3 months ago
    df["lag_12"] = df[TARGET_COL].shift(12)   # same month last year

    # Drop rows where lag features don't exist yet (first 12 rows)
    df = df.dropna(subset=["lag_1", "lag_3", "lag_12"]).reset_index(drop=True)

    return df


def scale_features(X_train: np.ndarray, X_test: np.ndarray):
    """
    Normalize features to zero mean and unit variance (Z-score normalization).

    WHY SCALE?
      MLP is sensitive to the scale of inputs.
      - lag_12 might be in the hundreds of thousands (e.g. 200,000 tourists)
      - is_covid is 0 or 1
      Without scaling, the large values would dominate and the model would
      effectively ignore the small-valued features.

    IMPORTANT — Fit scaler on TRAINING data only:
      We compute mean and std from training data, then apply those same
      values to the test data. Using test data to fit the scaler would
      leak future information into the past ("data leakage").

    Args:
        X_train: Training features array, shape (n_train, n_features)
        X_test:  Test features array,     shape (n_test,  n_features)

    Returns:
        X_train_scaled, X_test_scaled, scaler_params dict
    """
    mean = X_train.mean(axis=0)
    std  = X_train.std(axis=0)
    std[std == 0] = 1.0   # prevent division by zero for constant features

    X_train_scaled = (X_train - mean) / std
    X_test_scaled  = (X_test  - mean) / std

    return X_train_scaled, X_test_scaled, {"mean": mean, "std": std}


def scale_target(y_train: np.ndarray, y_test: np.ndarray):
    """
    Scale the target variable (tourist arrivals) the same way.
    MLP benefits from having the output in a normalized range too.

    Returns:
        y_train_scaled, y_test_scaled, scaler_params dict
    """
    mean = float(y_train.mean())
    std  = float(y_train.std())
    if std == 0:
        std = 1.0

    y_train_scaled = (y_train - mean) / std
    y_test_scaled  = (y_test  - mean) / std

    return y_train_scaled, y_test_scaled, {"mean": mean, "std": std}


def inverse_scale_target(y_scaled: np.ndarray, scaler_params: dict) -> np.ndarray:
    """
    Convert scaled predictions back to actual tourist arrival counts.
    Call this after MLP prediction to get real numbers.
    """
    return y_scaled * scaler_params["std"] + scaler_params["mean"]


def prepare_data() -> dict:
    """
    Complete pipeline:
      Load CSV → Add features → Train/test split → Scale

    Returns a dict containing everything train.py needs.
    """
    if not os.path.exists(PROCESSED_CSV):
        raise FileNotFoundError(
            f"Processed CSV not found at {PROCESSED_CSV}\n"
            "Run data cleaning first:\n"
            "  python utils/data_cleaner.py ntb"
        )

    df = pd.read_csv(PROCESSED_CSV, parse_dates=["date"])
    df = add_features(df)

    # ── Train / Test split ─────────────────────────────────────────────────────
    # We use the last TEST_MONTHS months as the test set.
    # WHY? In time series, you must always test on the future —
    # never randomly shuffle and split, as that leaks future info into training.
    train_df = df.iloc[:-TEST_MONTHS].copy()
    test_df  = df.iloc[-TEST_MONTHS:].copy()

    X_train = train_df[FEATURE_COLS].values
    y_train = train_df[TARGET_COL].values.reshape(-1, 1)
    X_test  = test_df[FEATURE_COLS].values
    y_test  = test_df[TARGET_COL].values.reshape(-1, 1)

    # Scale
    X_train_sc, X_test_sc, feat_scaler = scale_features(X_train, X_test)
    y_train_sc, y_test_sc, tgt_scaler  = scale_target(y_train, y_test)

    print(f"  Training months : {len(train_df)}")
    print(f"  Test months     : {len(test_df)}")
    print(f"  Features used   : {FEATURE_COLS}")

    return {
        "X_train":     X_train_sc,
        "y_train":     y_train_sc,
        "X_test":      X_test_sc,
        "y_test":      y_test_sc,
        "feat_scaler": feat_scaler,
        "tgt_scaler":  tgt_scaler,
        "train_df":    train_df,
        "test_df":     test_df,
        "full_df":     df,
    }
