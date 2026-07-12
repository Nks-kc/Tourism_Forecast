from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from config import PROCESSED_TOTAL_CSV, TEST_MONTHS
from feature_engineering.constants import DATE_COLUMN, COUNTRY_COLUMN, TARGET_COLUMN
from feature_engineering.cross_validation import run_cross_validation
from feature_engineering.preprocessing import preprocess_data
from feature_engineering.features import (
    add_time_features,
    add_rolling_features,
    remove_initial_rolling_rows,
    add_lag_features,
    remove_initial_nan_rows,
)
from feature_engineering.dataset import get_feature_columns, get_target_column
from models.scaler import StandardScaler

logger = logging.getLogger(__name__)
TOTAL_PSEUDO_COUNTRY = "Total"


def build_total_features(reconciled_df: pd.DataFrame | None = None) -> pd.DataFrame:
    if reconciled_df is None:
        reconciled_df = run_cross_validation()
    total_df = reconciled_df.groupby(DATE_COLUMN, as_index=False)[TARGET_COLUMN].sum()
    total_df[COUNTRY_COLUMN] = TOTAL_PSEUDO_COUNTRY
    total_df = preprocess_data(total_df)
    total_df = add_time_features(total_df)
    total_df = add_lag_features(total_df)
    total_df = add_rolling_features(total_df)
    total_df = remove_initial_nan_rows(total_df)
    total_df = remove_initial_rolling_rows(total_df)
    Path(PROCESSED_TOTAL_CSV).parent.mkdir(parents=True, exist_ok=True)
    total_df.to_csv(PROCESSED_TOTAL_CSV, index=False)
    logger.info(
        "Total-series processed dataset saved to %s (%d rows)",
        PROCESSED_TOTAL_CSV,
        len(total_df),
    )
    return total_df


@dataclass
class TotalTrainingData:
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


def prepare_total_training_data(test_months: int = TEST_MONTHS) -> TotalTrainingData:
    if not Path(PROCESSED_TOTAL_CSV).exists():
        build_total_features()
    df = pd.read_csv(PROCESSED_TOTAL_CSV)
    feature_columns = get_feature_columns(df)
    target_column = get_target_column()
    df = df.sort_values(DATE_COLUMN).reset_index(drop=True)
    if len(df) <= test_months:
        raise ValueError(
            f"Total series has only {len(df)} observations. Cannot reserve {test_months} months for testing."
        )
    train_df = df.iloc[:-test_months].reset_index(drop=True)
    test_df = df.iloc[-test_months:].reset_index(drop=True)
    X_train = train_df[feature_columns].values
    X_test = test_df[feature_columns].values
    y_train = train_df[[target_column]].values
    y_test = test_df[[target_column]].values
    feature_scaler = StandardScaler()
    X_train = feature_scaler.fit_transform(X_train)
    X_test = feature_scaler.transform(X_test)
    target_scaler = StandardScaler()
    y_train = target_scaler.fit_transform(y_train)
    y_test = target_scaler.transform(y_test)
    return TotalTrainingData(
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    df = build_total_features()
    print(df.tail())
