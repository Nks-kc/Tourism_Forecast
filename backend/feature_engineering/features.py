from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from feature_engineering.constants import (
    AUTUMN_MONTHS,
    COUNTRY_COLUMN,
    COVID_END,
    COVID_START,
    DATE_COLUMN,
    LAG_MONTHS,
    MONSOON_MONTHS,
    MONTH_COLUMN,
    MONTHS_IN_YEAR,
    ROLLING_WINDOWS,
    SPRING_MONTHS,
    TARGET_COLUMN,
)

logger = logging.getLogger(__name__)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Generating time features...")
    df = df.copy()
    radians = 2 * np.pi * (df[MONTH_COLUMN] - 1) / MONTHS_IN_YEAR
    df["month_sin"] = np.sin(radians)
    df["month_cos"] = np.cos(radians)
    df["time_index"] = df.groupby(COUNTRY_COLUMN).cumcount()
    df["is_covid"] = (
        (df[DATE_COLUMN] >= pd.Timestamp(COVID_START))
        & (df[DATE_COLUMN] <= pd.Timestamp(COVID_END))
    ).astype(int)
    df["is_spring_trek"] = df[MONTH_COLUMN].isin(SPRING_MONTHS).astype(int)
    df["is_autumn_trek"] = df[MONTH_COLUMN].isin(AUTUMN_MONTHS).astype(int)
    df["is_monsoon"] = df[MONTH_COLUMN].isin(MONSOON_MONTHS).astype(int)
    logger.info("Time features generated successfully.")
    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Generating lag features...")
    df = df.copy()
    df = df.sort_values(by=[COUNTRY_COLUMN, DATE_COLUMN]).reset_index(drop=True)
    grouped = df.groupby(COUNTRY_COLUMN)
    for lag in LAG_MONTHS:
        column_name = f"lag_{lag}"
        logger.info("Creating %s", column_name)
        df[column_name] = grouped[TARGET_COLUMN].shift(lag)
    logger.info("Lag feature generation complete.")
    return df


def remove_initial_nan_rows(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Removing rows with missing lag values...")
    lag_columns = [f"lag_{lag}" for lag in LAG_MONTHS]
    before = len(df)
    df = df.dropna(subset=lag_columns).reset_index(drop=True)
    removed = before - len(df)
    logger.info("Removed %d rows due to lag initialization.", removed)
    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Generating rolling features...")
    df = df.copy()
    df = df.sort_values(by=[COUNTRY_COLUMN, DATE_COLUMN]).reset_index(drop=True)
    grouped = df.groupby(COUNTRY_COLUMN)
    for window in ROLLING_WINDOWS:
        mean_column = f"rolling_mean_{window}"
        std_column = f"rolling_std_{window}"
        logger.info("Creating %s", mean_column)
        logger.info("Creating %s", std_column)
        history = grouped[TARGET_COLUMN].shift(1)
        df[mean_column] = history.rolling(window=window, min_periods=window).mean()
        df[std_column] = history.rolling(window=window, min_periods=window).std()
    logger.info("Rolling features generated successfully.")
    return df


def remove_initial_rolling_rows(df: pd.DataFrame) -> pd.DataFrame:
    rolling_columns = []
    for window in ROLLING_WINDOWS:
        rolling_columns.extend([f"rolling_mean_{window}", f"rolling_std_{window}"])
    before = len(df)
    df = df.dropna(subset=rolling_columns).reset_index(drop=True)
    removed = before - len(df)
    logger.info("Removed %d rows with incomplete rolling statistics.", removed)
    return df
