"""
Utilities for working with the processed feature dataset.

This module provides helper functions that are used by the
training and prediction pipelines. It intentionally does NOT
perform feature engineering itself—it simply loads the processed
dataset and determines which columns are model features.
"""

from __future__ import annotations

import pandas as pd

from config import PROCESSED_CSV
from feature_engineering.constants import (
    DATE_COLUMN,
    YEAR_COLUMN,
    MONTH_COLUMN,
    TARGET_COLUMN,
    COUNTRY_COLUMN,
)


# ---------------------------------------------------------------------
# Columns that should never be used as model inputs.
# ---------------------------------------------------------------------

EXCLUDED_COLUMNS = {
    DATE_COLUMN,
    YEAR_COLUMN,
    MONTH_COLUMN,
    TARGET_COLUMN,
    COUNTRY_COLUMN,
}


# ---------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------


def load_processed_dataset() -> pd.DataFrame:
    """
    Load the processed feature dataset.

    Returns
    -------
    pd.DataFrame
        Processed dataset produced by the feature engineering pipeline.
    """
    return pd.read_csv(PROCESSED_CSV)


# ---------------------------------------------------------------------
# Feature discovery
# ---------------------------------------------------------------------


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Automatically determine which columns are model features.

    Any column that is not metadata or the target variable is treated
    as an input feature.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    list[str]
    """

    return [column for column in df.columns if column not in EXCLUDED_COLUMNS]


# ---------------------------------------------------------------------
# Target column
# ---------------------------------------------------------------------


def get_target_column() -> str:
    """
    Return the name of the prediction target.
    """

    return TARGET_COLUMN
