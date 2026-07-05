"""
Utilities for preparing training data for forecasting models.

This module replaces the old `prepare_data()` function from the previous
project structure. It is responsible for:

- Loading the processed feature dataset.
- Selecting model input features.
- Splitting into train/test sets.
- Scaling features and target.
- Returning everything required by the training pipeline.
"""

from __future__ import annotations
from feature_engineering.constants import COUNTRY_PREFIX
from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import TEST_MONTHS

from feature_engineering.dataset import (
    load_processed_dataset,
    get_feature_columns,
    get_target_column,
)

from models.scaler import StandardScaler


# =============================================================================
# Training Dataset
# =============================================================================


@dataclass
class TrainingData:
    dataframe: pd.DataFrame

    train_df: pd.DataFrame
    test_df: pd.DataFrame

    X_train: np.ndarray
    X_test: np.ndarray

    y_train: np.ndarray
    y_test: np.ndarray

    feature_scaler: StandardScaler
    target_scaler: StandardScaler

    feature_columns: list[str]
    target_column: str


# =============================================================================
# Main function
# =============================================================================


def prepare_training_data(
    test_months: int = TEST_MONTHS,
) -> TrainingData:
    """
    Load the processed dataset and prepare it for model training.
    """

    # ----------------------------------------------------------
    # Load processed dataset
    # ----------------------------------------------------------

    df = load_processed_dataset()

    # ----------------------------------------------------------
    # Recover country labels from one-hot encoded columns
    # ----------------------------------------------------------

    country_columns = [
        column
        for column in df.columns
        if column.startswith(f"{COUNTRY_PREFIX}_")
    ]

    if not country_columns:
        raise ValueError(
            "No one-hot encoded country columns found in processed dataset."
        )

    df["country"] = (
        df[country_columns]
        .idxmax(axis=1)
        .str.replace(f"{COUNTRY_PREFIX}_", "", regex=False)
    )

    feature_columns = get_feature_columns(df)

    target_column = get_target_column()

    # ----------------------------------------------------------
    # Train / Test Split (Per Country)
    # ----------------------------------------------------------

    train_parts = []

    test_parts = []

    for _, country_df in df.groupby("country"):

        country_df = country_df.sort_values("date").reset_index(drop=True)

        if len(country_df) <= test_months:
            raise ValueError(
                f"Country has only {len(country_df)} observations. "
                f"Cannot reserve {test_months} months for testing."
            )

        train_parts.append(
            country_df.iloc[:-test_months]
        )

        test_parts.append(
            country_df.iloc[-test_months:]
        )

    train_df = (
        pd.concat(train_parts)
        .sort_values(["country", "date"])
        .reset_index(drop=True)
    )

    test_df = (
        pd.concat(test_parts)
        .sort_values(["country", "date"])
        .reset_index(drop=True)
    )

    # ----------------------------------------------------------
    # Features / Target
    # ----------------------------------------------------------

    X_train = train_df[feature_columns].values

    X_test = test_df[feature_columns].values

    y_train = train_df[[target_column]].values

    y_test = test_df[[target_column]].values

    # ----------------------------------------------------------
    # Feature Scaling
    # ----------------------------------------------------------

    feature_scaler = StandardScaler()

    X_train = feature_scaler.fit_transform(X_train)

    X_test = feature_scaler.transform(X_test)

    # ----------------------------------------------------------
    # Target Scaling
    # ----------------------------------------------------------

    target_scaler = StandardScaler()

    y_train = target_scaler.fit_transform(y_train)

    y_test = target_scaler.transform(y_test)

    # ----------------------------------------------------------
    # Return
    # ----------------------------------------------------------

    return TrainingData(
        dataframe=df,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        train_df=train_df,
        test_df=test_df,
        feature_scaler=feature_scaler,
        target_scaler=target_scaler,
        feature_columns=feature_columns,
        target_column=target_column,
    )
