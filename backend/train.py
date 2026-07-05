"""
Train all forecasting models.

This script:

1. Loads the processed dataset.
2. Prepares train/test splits.
3. Trains every model.
4. Evaluates each model.
5. Saves trained models.
6. Saves evaluation metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from config import (
    SAVED_MODELS_DIR,
    LR_MODEL_FILENAME,
)

from feature_engineering.training_data import (
    prepare_training_data,
)

from models.mlp import MLP
from models.linear_regression_model import LinearRegressionModel
from models.sarima_model import SARIMAModel
from models.holtwinters_model import HoltWintersModel

from evaluation.metrics import Metrics


# ============================================================
# Model Training Functions
# ============================================================


def train_mlp(data):

    print("\nTraining MLP...")

    model = MLP(input_size=len(data.feature_columns))

    history = model.train(
        data.X_train,
        data.y_train,
        val_data=(data.X_test, data.y_test),
        verbose=True,
    )

    predictions = model.predict(data.X_test)

    predictions = data.target_scaler.inverse_transform(predictions)

    actual = data.target_scaler.inverse_transform(data.y_test)

    metrics = Metrics.evaluate(
        actual,
        predictions,
    )

    model.save_model(Path(SAVED_MODELS_DIR) / "mlp.npz")

    return metrics, history


def train_linear_regression(data):

    print("\nTraining Linear Regression...")

    model = LinearRegressionModel()

    model.fit(
        data.X_train,
        data.y_train,
        feature_names=data.feature_columns,
    )

    predictions = model.predict(data.X_test)

    predictions = data.target_scaler.inverse_transform(predictions)

    actual = data.target_scaler.inverse_transform(data.y_test)

    metrics = Metrics.evaluate(
        actual,
        predictions,
    )

    model.save(str(Path(SAVED_MODELS_DIR) / LR_MODEL_FILENAME))

    return metrics


def train_sarima(data):

    print("\nTraining SARIMA...")

    exog_columns = [
        "is_spring_trek",
        "is_autumn_trek",
        "is_monsoon",
        "is_covid",
    ]

    save_dir = Path(SAVED_MODELS_DIR) / "sarima"
    save_dir.mkdir(parents=True, exist_ok=True)

    country_metrics = []

    countries = sorted(data.train_df["country"].unique())

    def safe_filename(country: str) -> str:
        return country.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")

    fallback_count = 0
    for country in countries:
        print(f"\nTraining SARIMA for {country}...")

        train_country = (
            data.train_df[data.train_df["country"] == country]
            .sort_values("date")
            .reset_index(drop=True)
        )

        test_country = (
            data.test_df[data.test_df["country"] == country]
            .sort_values("date")
            .reset_index(drop=True)
        )

        train_y = train_country[data.target_column].values
        test_y = test_country[data.target_column].values

        train_exog = train_country[exog_columns].values
        test_exog = test_country[exog_columns].values

        try:
            model = SARIMAModel()

            model.fit(
                train_y,
                exog_train=train_exog,
            )

            predictions = model.predict(
                steps=len(test_country),
                exog_future=test_exog,
            )

            predictions = np.asarray(predictions)

            if (
                np.any(np.isnan(predictions))
                or np.any(np.isinf(predictions))
                or np.max(np.abs(predictions)) > 1_000_000
            ):
                raise ValueError("Unstable forecast")

        except Exception as e:
            fallback_count += 1
            print(f"  Default SARIMA failed ({e})")
            print("  Retrying with simpler SARIMA...")

            try:
                model = SARIMAModel(
                    order=(1, 1, 0),
                    seasonal_order=(0, 1, 1, 12),
                )

                model.fit(
                    train_y,
                    exog_train=train_exog,
                )

                predictions = model.predict(
                    steps=len(test_country),
                    exog_future=test_exog,
                )

                predictions = np.asarray(predictions)

                if (
                    np.any(np.isnan(predictions))
                    or np.any(np.isinf(predictions))
                    or np.max(np.abs(predictions)) > 1_000_000
                ):
                    raise ValueError("Fallback SARIMA also unstable")

            except Exception as e:
                print(f"  Skipping {country}: {e}")
                continue

        metrics = Metrics.evaluate(test_y, predictions)

        print(
            f"{country:<15}"
            f" MAE={metrics['MAE']:.2f}"
            f" RMSE={metrics['RMSE']:.2f}"
            f" MAPE={metrics['MAPE']:.2f}%"
        )

        country_metrics.append(metrics)

        model.save(str(save_dir / (safe_filename(country) + ".pkl")))

    print(f"\nSARIMA fallback used for {fallback_count} countries.")

    if not country_metrics:
        raise RuntimeError("No SARIMA models trained successfully.")

    average_metrics = {
        "MAE": round(np.mean([m["MAE"] for m in country_metrics]), 2),
        "RMSE": round(np.mean([m["RMSE"] for m in country_metrics]), 2),
        "MAPE": round(np.mean([m["MAPE"] for m in country_metrics]), 2),
    }

    return average_metrics


def train_holt_winters(data):

    print("\nTraining Holt-Winters...")

    save_dir = Path(SAVED_MODELS_DIR) / "holtwinters"
    save_dir.mkdir(parents=True, exist_ok=True)

    country_metrics = []

    countries = sorted(data.train_df["country"].unique())

    for country in countries:
        print(f"  Training Holt-Winters for {country}...")

        train_country = (
            data.train_df[data.train_df["country"] == country]
            .sort_values("date")
            .reset_index(drop=True)
        )

        test_country = (
            data.test_df[data.test_df["country"] == country]
            .sort_values("date")
            .reset_index(drop=True)
        )

        model = HoltWintersModel()

        model.fit(train_country[data.target_column].values)

        predictions = model.predict(len(test_country))

        actual = test_country[data.target_column].values

        metrics = Metrics.evaluate(actual, predictions)

        country_metrics.append(metrics)

        filename = country.replace(" ", "_") + ".pkl"

        model.save(str(save_dir / filename))

    average_metrics = {
        "MAE": round(np.mean([m["MAE"] for m in country_metrics]), 2),
        "RMSE": round(np.mean([m["RMSE"] for m in country_metrics]), 2),
        "MAPE": round(np.mean([m["MAPE"] for m in country_metrics]), 2),
    }

    return average_metrics


# ============================================================
# Main
# ============================================================


def main():

    print("=" * 60)
    print("Tourism Forecast Training")
    print("=" * 60)

    Path(SAVED_MODELS_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    data = prepare_training_data()

    results = {}

    mlp_metrics, history = train_mlp(data)
    results["MLP"] = mlp_metrics

    lr_metrics = train_linear_regression(data)
    results["Linear Regression"] = lr_metrics

    sarima_metrics = train_sarima(data)
    results["SARIMA"] = sarima_metrics

    hw_metrics = train_holt_winters(data)
    results["Holt-Winters"] = hw_metrics

    Metrics.print_results(results)

    Metrics.save_results(
        results,
        Path(SAVED_MODELS_DIR) / "results.json",
    )

    with open(
        Path(SAVED_MODELS_DIR) / "mlp_history.json",
        "w",
    ) as f:
        json.dump(
            history,
            f,
            indent=4,
        )

    print("\nTraining completed successfully.")
    print(f"Models saved to: {SAVED_MODELS_DIR}")

if __name__ == "__main__":
    main()
