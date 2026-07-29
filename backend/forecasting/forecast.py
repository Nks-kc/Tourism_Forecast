from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from config import (
    LR_MODEL_FILENAME,
    PROCESSED_TOTAL_CSV,
    SAVED_MODELS_DIR,
    SAVED_MODELS_TOTAL_DIR,
    SCALER_FILENAME,
    TOTAL_LR_MODEL_FILENAME,
    TOTAL_SCALER_FILENAME,
)
from feature_engineering.constants import SEASON_FLAG_COLUMNS
from feature_engineering.dataset import (
    get_feature_columns,
    get_target_column,
    load_processed_dataset,
)
from forecasting.recursive import RecursiveForecaster
from forecasting.utils import next_month, update_season_flags
from models.holtwinters_model import HoltWintersModel
from models.linear_regression_model import LinearRegressionModel
from models.mlp import MLP
from models.sarima_model import SARIMAModel
from models.scaler import StandardScaler


@lru_cache(maxsize=1)
def _cached_dataset() -> pd.DataFrame:
    df = load_processed_dataset()
    country_columns = [column for column in df.columns if column.startswith("country_")]
    if not country_columns:
        raise ValueError(
            "No one-hot encoded country columns found in processed dataset."
        )
    df["country"] = (
        df[country_columns].idxmax(axis=1).str.replace("country_", "", regex=False)
    )
    return df


@lru_cache(maxsize=1)
def _cached_scalers() -> tuple[StandardScaler, StandardScaler]:
    scaler_path = Path(SAVED_MODELS_DIR) / SCALER_FILENAME
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Scalers not found at {scaler_path}. Run 'python train.py' first."
        )
    scaler_file = np.load(scaler_path, allow_pickle=True)
    feature_scaler = StandardScaler()
    feature_scaler.set_params(
        mean=scaler_file["feat_mean"], std=scaler_file["feat_std"]
    )
    target_scaler = StandardScaler()
    target_scaler.set_params(mean=scaler_file["tgt_mean"], std=scaler_file["tgt_std"])
    return (feature_scaler, target_scaler)


@lru_cache(maxsize=1)
def _cached_mlp_model() -> MLP:
    return MLP.load_model(str(Path(SAVED_MODELS_DIR) / "mlp.npz"))


@lru_cache(maxsize=1)
def _cached_linear_regression_model() -> LinearRegressionModel:
    return LinearRegressionModel.load_model(
        str(Path(SAVED_MODELS_DIR) / LR_MODEL_FILENAME)
    )


@lru_cache(maxsize=None)
def _cached_sarima_model(country: str) -> SARIMAModel:
    filename = _safe_filename(country) + ".pkl"
    model_path = Path(SAVED_MODELS_DIR) / "sarima" / filename
    if not model_path.exists():
        raise FileNotFoundError(
            f"No trained SARIMA model found for '{country}' at {model_path}."
        )
    return SARIMAModel.load_model(str(model_path))


@lru_cache(maxsize=None)
def _cached_holtwinters_model(country: str) -> HoltWintersModel:
    filename = _safe_filename(country) + ".pkl"
    model_path = Path(SAVED_MODELS_DIR) / "holtwinters" / filename
    if not model_path.exists():
        raise FileNotFoundError(
            f"No trained Holt-Winters model found for '{country}' at {model_path}."
        )
    return HoltWintersModel.load_model(str(model_path))


def get_dataset_last_date() -> pd.Timestamp:
    return pd.to_datetime(_cached_dataset()["date"]).max()


def _safe_filename(country: str) -> str:
    return country.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")


def _build_future_exog(last_date: pd.Timestamp, horizon: int) -> np.ndarray:
    rows = []
    current_date = last_date
    for _ in range(horizon):
        current_date = next_month(current_date)
        flags = update_season_flags(current_date)
        rows.append([flags[column] for column in SEASON_FLAG_COLUMNS])
    return np.asarray(rows, dtype=float)


def _get_country_history(country: str) -> pd.DataFrame:
    df = _cached_dataset()
    available_countries = sorted(df["country"].unique())
    if country not in available_countries:
        raise ValueError(
            f"Unknown country '{country}'. Available countries: {available_countries}"
        )
    history_df = (
        df[df["country"] == country].sort_values("date").reset_index(drop=True).copy()
    )
    return history_df


def forecast(model_name: str, country: str, horizon: int = 12) -> np.ndarray:
    model_name = model_name.lower().strip()
    if horizon <= 0:
        raise ValueError("horizon must be a positive integer.")
    history_df = _get_country_history(country)
    if model_name in ("mlp", "linear regression", "linear_regression"):
        feature_columns = get_feature_columns(history_df)
        target_column = get_target_column()
        feature_scaler, target_scaler = _cached_scalers()
        if model_name == "mlp":
            model = _cached_mlp_model()
        else:
            model = _cached_linear_regression_model()
        forecaster = RecursiveForecaster()
        return forecaster.forecast(
            model=model,
            history_df=history_df,
            feature_columns=feature_columns,
            target_column=target_column,
            feature_scaler=feature_scaler,
            target_scaler=target_scaler,
            horizon=horizon,
        )
    if model_name == "sarima":
        model = _cached_sarima_model(country)
        last_date = pd.to_datetime(history_df["date"]).max()
        exog_future = _build_future_exog(last_date, horizon)
        return model.predict(steps=horizon, exog_future=exog_future)
    if model_name in ("holt", "holtwinters", "holt-winters", "holt_winters"):
        model = _cached_holtwinters_model(country)
        return model.predict(horizon)
    raise ValueError(f"Unknown model '{model_name}'.")


@lru_cache(maxsize=1)
def _cached_total_dataset() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_TOTAL_CSV)


@lru_cache(maxsize=1)
def _cached_total_scalers() -> tuple[StandardScaler, StandardScaler]:
    scaler_path = Path(SAVED_MODELS_TOTAL_DIR) / TOTAL_SCALER_FILENAME
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Total-series scalers not found at {scaler_path}. Run 'python train.py' first."
        )
    scaler_file = np.load(scaler_path, allow_pickle=True)
    feature_scaler = StandardScaler()
    feature_scaler.set_params(
        mean=scaler_file["feat_mean"], std=scaler_file["feat_std"]
    )
    target_scaler = StandardScaler()
    target_scaler.set_params(mean=scaler_file["tgt_mean"], std=scaler_file["tgt_std"])
    return (feature_scaler, target_scaler)


@lru_cache(maxsize=1)
def _cached_total_mlp_model() -> MLP:
    return MLP.load_model(str(Path(SAVED_MODELS_TOTAL_DIR) / "mlp_total.npz"))


@lru_cache(maxsize=1)
def _cached_total_linear_regression_model() -> LinearRegressionModel:
    return LinearRegressionModel.load_model(
        str(Path(SAVED_MODELS_TOTAL_DIR) / TOTAL_LR_MODEL_FILENAME)
    )


@lru_cache(maxsize=1)
def _cached_total_sarima_model() -> SARIMAModel:
    return SARIMAModel.load_model(
        str(Path(SAVED_MODELS_TOTAL_DIR) / "sarima_total.pkl")
    )


@lru_cache(maxsize=1)
def _cached_total_holtwinters_model() -> HoltWintersModel:
    return HoltWintersModel.load_model(
        str(Path(SAVED_MODELS_TOTAL_DIR) / "holtwinters_total.pkl")
    )


def get_total_dataset_last_date() -> pd.Timestamp:
    return pd.to_datetime(_cached_total_dataset()["date"]).max()


def forecast_total(model_name: str, horizon: int = 12) -> np.ndarray:
    model_name = model_name.lower().strip()
    if horizon <= 0:
        raise ValueError("horizon must be a positive integer.")
    history_df = (
        _cached_total_dataset().sort_values("date").reset_index(drop=True).copy()
    )
    if model_name in ("mlp", "linear regression", "linear_regression"):
        feature_columns = get_feature_columns(history_df)
        target_column = get_target_column()
        feature_scaler, target_scaler = _cached_total_scalers()
        model = (
            _cached_total_mlp_model()
            if model_name == "mlp"
            else _cached_total_linear_regression_model()
        )
        forecaster = RecursiveForecaster()
        return forecaster.forecast(
            model=model,
            history_df=history_df,
            feature_columns=feature_columns,
            target_column=target_column,
            feature_scaler=feature_scaler,
            target_scaler=target_scaler,
            horizon=horizon,
        )
    if model_name == "sarima":
        model = _cached_total_sarima_model()
        last_date = pd.to_datetime(history_df["date"]).max()
        exog_future = _build_future_exog(last_date, horizon)
        return model.predict(steps=horizon, exog_future=exog_future)
    if model_name in ("holt", "holtwinters", "holt-winters", "holt_winters"):
        model = _cached_total_holtwinters_model()
        return model.predict(horizon)
    raise ValueError(f"Unknown model '{model_name}'.")
