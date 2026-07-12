from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd


@dataclass(slots=True)
class TrainingData:
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


@dataclass(slots=True)
class PredictionData:
    X_future: np.ndarray
    future_dates: pd.DatetimeIndex
    countries: List[str]
    feature_columns: List[str]


@dataclass(slots=True)
class PipelineMetadata:
    countries: List[str]
    start_date: str
    end_date: str
    total_rows: int
    feature_count: int
    forecast_horizon: int
    covid_period: tuple[str, str]


@dataclass(slots=True)
class ModelResult:
    model_name: str
    rmse: float
    mae: float
    mape: float
    predictions: np.ndarray
    actual: np.ndarray
    training_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
