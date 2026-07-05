"""
feature_engineering/encoding.py

Country encoding utilities.

Uses one-hot encoding so that machine learning models
can distinguish between countries without introducing
artificial ordering.

Author: Tourism Forecasting Project
"""

from __future__ import annotations

import logging

import pandas as pd

from feature_engineering.constants import (
    COUNTRY_COLUMN,
)

logger = logging.getLogger(__name__)


def encode_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encode the country column.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    logger.info("Encoding country feature...")

    df = df.copy()

    encoded = pd.get_dummies(
        df[COUNTRY_COLUMN],
        prefix="country",
        dtype=int,
    )

    df = pd.concat(
        [
            df.drop(columns=[COUNTRY_COLUMN]),
            encoded,
        ],
        axis=1,
    )

    logger.info(
        "Generated %d country features.",
        encoded.shape[1],
    )

    return df


def get_country_columns(df: pd.DataFrame) -> list[str]:
    """
    Return generated country columns.
    """

    return sorted(
        [
            column
            for column in df.columns
            if column.startswith("country_")
        ]
    )