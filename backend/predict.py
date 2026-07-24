from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from config import FORECAST_HORIZON, OUTPUTS_FORECASTS_DIR
from feature_engineering.dataset import get_available_countries
from forecasting.forecast import (
    forecast,
    forecast_total,
    get_dataset_last_date,
    get_total_dataset_last_date,
)
from forecasting.utils import next_month

AVAILABLE_MODELS = ["mlp", "linear_regression", "sarima", "holtwinters"]
MODEL_DISPLAY_NAMES = {
    "mlp": "MLP",
    "linear_regression": "Linear Regression",
    "sarima": "SARIMA",
    "holtwinters": "Holt-Winters",
}


def print_models() -> None:
    print("\nAvailable Models")
    print("-" * 30)
    for i, model in enumerate(AVAILABLE_MODELS, start=1):
        print(f"{i}. {model}")


def print_countries(countries: list[str]) -> None:
    print("\nAvailable Countries")
    print("-" * 30)
    for i, country in enumerate(countries, start=1):
        print(f"{i}. {country}")


def _future_month_labels(last_date, horizon: int) -> list[str]:
    labels = []
    current_date = last_date
    for _ in range(horizon):
        current_date = next_month(current_date)
        labels.append(current_date.strftime("%Y-%m"))
    return labels


def _save_forecast_csv(rows: list[dict], fieldnames: list[str], filename: str) -> Path:
    Path(OUTPUTS_FORECASTS_DIR).mkdir(parents=True, exist_ok=True)
    path = Path(OUTPUTS_FORECASTS_DIR) / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def predict_total(horizon: int = FORECAST_HORIZON, save_to_disk: bool = False) -> dict:
    if horizon <= 0:
        raise ValueError("horizon must be a positive integer.")
    months = _future_month_labels(get_total_dataset_last_date(), horizon)
    results = {}
    for model_key in AVAILABLE_MODELS:
        display_name = MODEL_DISPLAY_NAMES[model_key]
        try:
            values = forecast_total(model_name=model_key, horizon=horizon)
            values = [max(0.0, float(v)) for v in values]
            results[display_name] = {
                "months": months,
                "arrivals": [round(v, 2) for v in values],
            }
        except Exception as exc:  # noqa: BLE001
            # Skip models that fail to load or forecast (e.g. pickle version mismatch)
            import logging
            logging.getLogger(__name__).warning(
                "Skipping model '%s' in predict_total: %s", display_name, exc
            )
    if not results:
        raise RuntimeError(
            "All models failed to generate forecasts. Run 'python train.py' to retrain."
        )
    if save_to_disk:
        rows = [
            {"month": month, **{name: results[name]["arrivals"][i] for name in results}}
            for i, month in enumerate(months)
        ]
        fieldnames = ["month"] + list(results.keys())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = _save_forecast_csv(
            rows, fieldnames, f"nationwide_total_forecast_h{horizon}_{timestamp}.csv"
        )
        print(f"Forecast exported to: {path}")
    return results


def predict_country(
    country: str, horizon: int = FORECAST_HORIZON, save_to_disk: bool = False
) -> dict:
    if horizon <= 0:
        raise ValueError("horizon must be a positive integer.")
    available_countries = get_available_countries()
    if country not in available_countries:
        raise ValueError(
            f"Unknown country '{country}'. Available countries: {available_countries}"
        )
    months = _future_month_labels(get_dataset_last_date(), horizon)
    results = {}
    for model_key in AVAILABLE_MODELS:
        display_name = MODEL_DISPLAY_NAMES[model_key]
        values = forecast(model_name=model_key, country=country, horizon=horizon)
        values = [max(0.0, float(v)) for v in values]
        results[display_name] = {
            "months": months,
            "arrivals": [round(v, 2) for v in values],
        }
    if save_to_disk:
        rows = [
            {"month": month, **{name: results[name]["arrivals"][i] for name in results}}
            for i, month in enumerate(months)
        ]
        fieldnames = ["month"] + list(results.keys())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_country = country.replace(" ", "_")
        path = _save_forecast_csv(
            rows, fieldnames, f"{safe_country}_forecast_h{horizon}_{timestamp}.csv"
        )
        print(f"Forecast exported to: {path}")
    return results


def main():
    print("=" * 60)
    print("Tourism Forecast Prediction")
    print("=" * 60)
    print_models()
    model_choice = int(input("\nSelect model: "))
    model = AVAILABLE_MODELS[model_choice - 1]
    print("\nForecast scope")
    print("-" * 30)
    print("1. Nationwide total (all countries combined)")
    print("2. A specific country")
    scope_choice = input("\nSelect scope [1]: ").strip() or "1"
    country = None
    if scope_choice == "2":
        countries = get_available_countries()
        print_countries(countries)
        country_choice = int(input("\nSelect country: "))
        country = countries[country_choice - 1]
    horizon_input = input(f"\nForecast horizon [{FORECAST_HORIZON}]: ").strip()
    horizon = int(horizon_input) if horizon_input else FORECAST_HORIZON
    print("\nGenerating forecast...\n")
    if country is not None:
        predictions = forecast(model_name=model, country=country, horizon=horizon)
        months = _future_month_labels(get_dataset_last_date(), horizon)
        label = f"{country} ({model})"
        safe_name = country.replace(" ", "_")
    else:
        predictions = forecast_total(model_name=model, horizon=horizon)
        months = _future_month_labels(get_total_dataset_last_date(), horizon)
        label = f"Nationwide total ({model})"
        safe_name = "nationwide_total"
    print("-" * 50)
    print(label)
    print("-" * 50)
    for month, value in zip(months, predictions):
        print(f"{month}: {float(value):10.0f}")
    print("-" * 50)
    rows = [
        {"month": month, "arrivals": round(float(value), 2)}
        for month, value in zip(months, predictions)
    ]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = _save_forecast_csv(
        rows,
        fieldnames=["month", "arrivals"],
        filename=f"{safe_name}_{model}_{timestamp}.csv",
    )
    print(f"Forecast exported to: {path}")


if __name__ == "__main__":
    main()
