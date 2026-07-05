"""
Time-based feature engineering.

Generates cyclical month encoding, COVID flag,
seasonal flags and per-country time index.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd

from feature_engineering.constants import (
    DATE_COLUMN,
    MONTH_COLUMN,
    COUNTRY_COLUMN,
    COVID_START,
    COVID_END,
    MONTHS_IN_YEAR,
    SPRING_MONTHS,
    AUTUMN_MONTHS,
    MONSOON_MONTHS,
)

logger = logging.getLogger(__name__)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all calendar-based features.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """

    logger.info("Generating time features...")

    df = df.copy()

    # -------------------------
    # Month Cyclical Encoding
    # -------------------------

    radians = (
        2 * np.pi * (df[MONTH_COLUMN] - 1)
        / MONTHS_IN_YEAR
    )

    df["month_sin"] = np.sin(radians)

    df["month_cos"] = np.cos(radians)

    # -------------------------
    # Per-country time index
    # -------------------------

    df["time_index"] = (
        df.groupby(COUNTRY_COLUMN)
          .cumcount()
    )

    # -------------------------
    # COVID flag
    # -------------------------

    df["is_covid"] = (
        (df[DATE_COLUMN] >= pd.Timestamp(COVID_START))
        &
        (df[DATE_COLUMN] <= pd.Timestamp(COVID_END))
    ).astype(int)

    # -------------------------
    # Tourism seasons
    # -------------------------

    df["is_spring_trek"] = (
        df[MONTH_COLUMN]
        .isin(SPRING_MONTHS)
        .astype(int)
    )

    df["is_autumn_trek"] = (
        df[MONTH_COLUMN]
        .isin(AUTUMN_MONTHS)
        .astype(int)
    )

    df["is_monsoon"] = (
        df[MONTH_COLUMN]
        .isin(MONSOON_MONTHS)
        .astype(int)
    )

    logger.info("Time features generated successfully.")

    return df