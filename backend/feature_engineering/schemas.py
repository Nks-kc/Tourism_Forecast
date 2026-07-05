"""
feature_engineering/schemas.py

Dataclasses used throughout the tourism forecasting pipeline.

These classes improve readability by replacing loosely structured
dictionaries with typed objects.

Author: Tourism Forecasting Project
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

import numpy as np
import pandas as pd


# =============================================================================
# Training Dataset
# =============================================================================

@dataclass(slots=True)
class TrainingData:
    """
    Stores all data required during model training.
    """

    X_train: np.ndarray
    X_test: np.ndarray

    y_train: np.ndarray
    y_test: np.ndarray

    train_df: pd.DataFrame
    test_df: pd.DataFrame

    feature_columns: List[str]

    target_column: str

    feature_scaler: Optional[Any] = None

    target_scaler: Optional[Any] = None


# =============================================================================
# Prediction Dataset
# =============================================================================

@dataclass(slots=True)
class PredictionData:
    """
    Stores feature matrix used for forecasting.
    """

    X_future: np.ndarray

    future_dates: pd.DatetimeIndex

    countries: List[str]

    feature_columns: List[str]


# =============================================================================
# Pipeline Metadata
# =============================================================================

@dataclass(slots=True)
class PipelineMetadata:
    """
    Stores metadata generated during preprocessing.
    """

    countries: List[str]

    start_date: str

    end_date: str

    total_rows: int

    feature_count: int

    forecast_horizon: int

    covid_period: tuple[str, str]


# =============================================================================
# Model Result
# =============================================================================

@dataclass(slots=True)
class ModelResult:
    """
    Stores evaluation results of a forecasting model.
    """

    model_name: str

    rmse: float

    mae: float

    mape: float

    predictions: np.ndarray

    actual: np.ndarray

    training_time: float

    metadata: Dict[str, Any] = field(default_factory=dict)