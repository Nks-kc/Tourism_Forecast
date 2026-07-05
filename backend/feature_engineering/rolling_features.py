"""
feature_engineering/rolling_features.py

Creates rolling statistical features for each country's
monthly tourist arrivals.

Rolling statistics are calculated using only historical
observations to prevent target leakage.

Author: Tourism Forecasting Project
"""

from __future__ import annotations

import logging

import pandas as pd

from feature_engineering.constants import (
    COUNTRY_COLUMN,
    TARGET_COLUMN,
    ROLLING_WINDOWS,
    DATE_COLUMN
)

logger = logging.getLogger(__name__)


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate rolling statistics for each country.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    logger.info("Generating rolling features...")

    df = df.copy()

    df = df.sort_values(
        by=[COUNTRY_COLUMN, DATE_COLUMN]
    ).reset_index(drop=True)

    grouped = df.groupby(COUNTRY_COLUMN)

    for window in ROLLING_WINDOWS:

        mean_column = f"rolling_mean_{window}"
        std_column = f"rolling_std_{window}"

        logger.info("Creating %s", mean_column)
        logger.info("Creating %s", std_column)

        history = grouped[TARGET_COLUMN].shift(1)

        df[mean_column] = (
            history
            .rolling(
                window=window,
                min_periods=window,
            )
            .mean()
        )

        df[std_column] = (
            history
            .rolling(
                window=window,
                min_periods=window,
            )
            .std()
        )

    logger.info("Rolling features generated successfully.")

    return df


def remove_initial_rolling_rows(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove rows with missing rolling statistics.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    rolling_columns = []

    for window in ROLLING_WINDOWS:

        rolling_columns.extend(
            [
                f"rolling_mean_{window}",
                f"rolling_std_{window}",
            ]
        )

    before = len(df)

    df = (
        df.dropna(subset=rolling_columns)
          .reset_index(drop=True)
    )

    removed = before - len(df)

    logger.info(
        "Removed %d rows with incomplete rolling statistics.",
        removed,
    )

    return df