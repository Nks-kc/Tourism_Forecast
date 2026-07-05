"""
feature_engineering/lag_features.py

Creates lag-based features for each country's monthly tourist arrivals.

Lag features are generated independently for each country to prevent
data leakage between countries.

Author: Tourism Forecasting Project
"""

from __future__ import annotations

import logging

import pandas as pd

from feature_engineering.constants import (
    COUNTRY_COLUMN,
    TARGET_COLUMN,
    LAG_MONTHS,
    DATE_COLUMN,
)

logger = logging.getLogger(__name__)


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate lag features for each country.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
        DataFrame with lag features added.
    """

    logger.info("Generating lag features...")

    df = df.copy()

    # Ensure chronological order within each country
    df = df.sort_values(
        by=[COUNTRY_COLUMN, DATE_COLUMN]
    ).reset_index(drop=True)

    grouped = df.groupby(COUNTRY_COLUMN)

    for lag in LAG_MONTHS:

        column_name = f"lag_{lag}"

        logger.info("Creating %s", column_name)

        df[column_name] = (
            grouped[TARGET_COLUMN]
            .shift(lag)
        )

    logger.info("Lag feature generation complete.")

    return df


def remove_initial_nan_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows that contain NaN values introduced by lag features.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    logger.info(
        "Removing rows with missing lag values..."
    )

    lag_columns = [
        f"lag_{lag}"
        for lag in LAG_MONTHS
    ]

    before = len(df)

    df = df.dropna(
        subset=lag_columns
    ).reset_index(drop=True)

    removed = before - len(df)

    logger.info(
        "Removed %d rows due to lag initialization.",
        removed,
    )

    return df