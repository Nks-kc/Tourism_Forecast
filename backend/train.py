from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
import numpy as np
from config import (
    SAVED_MODELS_DIR,
    LR_MODEL_FILENAME,
    SCALER_FILENAME,
    OUTPUTS_LOGS_DIR,
    OUTPUTS_PLOTS_DIR,
    OUTPUTS_METRICS_DIR,
    OUTPUTS_FORECASTS_DIR,
    OUTPUTS_REPORTS_DIR,
    SAVED_MODELS_TOTAL_DIR,
    TOTAL_SCALER_FILENAME,
    TOTAL_LR_MODEL_FILENAME,
)
from feature_engineering.training_data import prepare_training_data
from feature_engineering.total_series import prepare_total_training_data
from feature_engineering.pipeline import run_pipeline
from models.mlp import MLP
from models.linear_regression_model import LinearRegressionModel
from models.sarima_model import SARIMAModel
from models.holtwinters_model import HoltWintersModel
from evaluation.metrics import Metrics
from evaluation.plotting import plot_training_loss, plot_model_comparison
from evaluation.comparison import ModelComparison
from evaluation.report import generate_html_report
from predict import predict_total


def save_scalers(data):
    scaler_path = Path(SAVED_MODELS_DIR) / SCALER_FILENAME
    np.savez(
        scaler_path,
        feat_mean=data.feature_scaler.mean_,
        feat_std=data.feature_scaler.std_,
        tgt_mean=data.target_scaler.mean_,
        tgt_std=data.target_scaler.std_,
    )
    print(f"Scalers saved to: {scaler_path}")


def save_total_scalers(data):
    Path(SAVED_MODELS_TOTAL_DIR).mkdir(parents=True, exist_ok=True)
    scaler_path = Path(SAVED_MODELS_TOTAL_DIR) / TOTAL_SCALER_FILENAME
    np.savez(
        scaler_path,
        feat_mean=data.feature_scaler.mean_,
        feat_std=data.feature_scaler.std_,
        tgt_mean=data.target_scaler.mean_,
        tgt_std=data.target_scaler.std_,
    )
    print(f"Total-series scalers saved to: {scaler_path}")


def train_mlp(data):
    print("\nTraining MLP...")
    model = MLP(input_size=len(data.feature_columns))
    history = model.train(
        data.X_train, data.y_train, val_data=(data.X_test, data.y_test), verbose=True
    )
    predictions = model.predict(data.X_test)
    predictions = data.target_scaler.inverse_transform(predictions)
    actual = data.target_scaler.inverse_transform(data.y_test)
    metrics = Metrics.evaluate(actual, predictions)
    model.save_model(Path(SAVED_MODELS_DIR) / "mlp.npz")
    return (metrics, history)


def train_linear_regression(data):
    print("\nTraining Linear Regression...")
    model = LinearRegressionModel()
    model.fit(data.X_train, data.y_train, feature_names=data.feature_columns)
    predictions = model.predict(data.X_test)
    predictions = data.target_scaler.inverse_transform(predictions)
    actual = data.target_scaler.inverse_transform(data.y_test)
    metrics = Metrics.evaluate(actual, predictions)
    model.save(str(Path(SAVED_MODELS_DIR) / LR_MODEL_FILENAME))
    return metrics


def train_sarima(data):
    print("\nTraining SARIMA...")
    exog_columns = ["is_spring_trek", "is_autumn_trek", "is_monsoon", "is_covid"]
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
            model.fit(train_y, exog_train=train_exog)
            predictions = model.predict(steps=len(test_country), exog_future=test_exog)
            predictions = np.asarray(predictions)
            if (
                np.any(np.isnan(predictions))
                or np.any(np.isinf(predictions))
                or np.max(np.abs(predictions)) > 1000000
            ):
                raise ValueError("Unstable forecast")
        except Exception as e:
            fallback_count += 1
            print(f"  Default SARIMA failed ({e})")
            print("  Retrying with simpler SARIMA...")
            try:
                model = SARIMAModel(order=(1, 1, 0), seasonal_order=(0, 1, 1, 12))
                model.fit(train_y, exog_train=train_exog)
                predictions = model.predict(
                    steps=len(test_country), exog_future=test_exog
                )
                predictions = np.asarray(predictions)
                if (
                    np.any(np.isnan(predictions))
                    or np.any(np.isinf(predictions))
                    or np.max(np.abs(predictions)) > 1000000
                ):
                    raise ValueError("Fallback SARIMA also unstable")
            except Exception as e:
                print(f"  Skipping {country}: {e}")
                continue
        metrics = Metrics.evaluate(test_y, predictions)
        print(
            f"{country:<15} MAE={metrics['MAE']:.2f} RMSE={metrics['RMSE']:.2f} MAPE={metrics['MAPE']:.2f}%"
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


def train_mlp_total(data):
    print("\nTraining MLP (Total)...")
    model = MLP(input_size=len(data.feature_columns))
    history = model.train(
        data.X_train, data.y_train, val_data=(data.X_test, data.y_test), verbose=True
    )
    predictions = model.predict(data.X_test)
    predictions = data.target_scaler.inverse_transform(predictions)
    actual = data.target_scaler.inverse_transform(data.y_test)
    metrics = Metrics.evaluate(actual, predictions)
    Path(SAVED_MODELS_TOTAL_DIR).mkdir(parents=True, exist_ok=True)
    model.save_model(Path(SAVED_MODELS_TOTAL_DIR) / "mlp_total.npz")
    return (metrics, history)


def train_linear_regression_total(data):
    print("\nTraining Linear Regression (Total)...")
    model = LinearRegressionModel()
    model.fit(data.X_train, data.y_train, feature_names=data.feature_columns)
    predictions = model.predict(data.X_test)
    predictions = data.target_scaler.inverse_transform(predictions)
    actual = data.target_scaler.inverse_transform(data.y_test)
    metrics = Metrics.evaluate(actual, predictions)
    Path(SAVED_MODELS_TOTAL_DIR).mkdir(parents=True, exist_ok=True)
    model.save(str(Path(SAVED_MODELS_TOTAL_DIR) / TOTAL_LR_MODEL_FILENAME))
    return metrics


def train_sarima_total(data):
    print("\nTraining SARIMA (Total)...")
    exog_columns = ["is_spring_trek", "is_autumn_trek", "is_monsoon", "is_covid"]
    train_y = data.train_df[data.target_column].values
    test_y = data.test_df[data.target_column].values
    train_exog = data.train_df[exog_columns].values
    test_exog = data.test_df[exog_columns].values
    try:
        model = SARIMAModel()
        model.fit(train_y, exog_train=train_exog)
        predictions = np.asarray(
            model.predict(steps=len(test_y), exog_future=test_exog)
        )
        if (
            np.any(np.isnan(predictions))
            or np.any(np.isinf(predictions))
            or np.max(np.abs(predictions)) > 1000000
        ):
            raise ValueError("Unstable forecast")
    except Exception as e:
        print(f"  Default SARIMA failed ({e})")
        print("  Retrying with simpler SARIMA...")
        model = SARIMAModel(order=(1, 1, 0), seasonal_order=(0, 1, 1, 12))
        model.fit(train_y, exog_train=train_exog)
        predictions = np.asarray(
            model.predict(steps=len(test_y), exog_future=test_exog)
        )
    metrics = Metrics.evaluate(test_y, predictions)
    Path(SAVED_MODELS_TOTAL_DIR).mkdir(parents=True, exist_ok=True)
    model.save(str(Path(SAVED_MODELS_TOTAL_DIR) / "sarima_total.pkl"))
    return metrics


def train_holt_winters_total(data):
    print("\nTraining Holt-Winters (Total)...")
    model = HoltWintersModel()
    model.fit(data.train_df[data.target_column].values)
    predictions = model.predict(len(data.test_df))
    actual = data.test_df[data.target_column].values
    metrics = Metrics.evaluate(actual, predictions)
    Path(SAVED_MODELS_TOTAL_DIR).mkdir(parents=True, exist_ok=True)
    model.save(str(Path(SAVED_MODELS_TOTAL_DIR) / "holtwinters_total.pkl"))
    return metrics


def main():
    run_started_at = datetime.now()
    print("=" * 60)
    print("Tourism Forecast Training")
    print("=" * 60)

    print("\n" + "-" * 60)
    print("Feature Engineering Pipeline")
    print("-" * 60)
    run_pipeline()  # regenerate processed_features from the latest raw data

    Path(SAVED_MODELS_DIR).mkdir(parents=True, exist_ok=True)
    Path(SAVED_MODELS_TOTAL_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUTS_LOGS_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUTS_PLOTS_DIR).mkdir(parents=True, exist_ok=True)
    print("\n" + "-" * 60)
    print("Per-country models")
    print("-" * 60)
    data = prepare_training_data()
    save_scalers(data)
    per_country_results = {}
    mlp_metrics, mlp_history = train_mlp(data)
    per_country_results["MLP"] = mlp_metrics
    per_country_results["Linear Regression"] = train_linear_regression(data)
    per_country_results["SARIMA"] = train_sarima(data)
    per_country_results["Holt-Winters"] = train_holt_winters(data)
    Metrics.print_results(per_country_results)
    Metrics.save_results(
        per_country_results, Path(SAVED_MODELS_DIR) / "results_per_country.json"
    )
    print("\n" + "-" * 60)
    print("Total-series models (nationwide aggregate)")
    print("-" * 60)
    total_data = prepare_total_training_data()
    save_total_scalers(total_data)
    total_results = {}
    mlp_total_metrics, mlp_total_history = train_mlp_total(total_data)
    total_results["MLP"] = mlp_total_metrics
    total_results["Linear Regression"] = train_linear_regression_total(total_data)
    total_results["SARIMA"] = train_sarima_total(total_data)
    total_results["Holt-Winters"] = train_holt_winters_total(total_data)
    Metrics.print_results(total_results)
    Metrics.save_results(total_results, Path(SAVED_MODELS_DIR) / "results.json")
    with open(Path(OUTPUTS_LOGS_DIR) / "mlp_training_history.json", "w") as f:
        json.dump(mlp_history, f, indent=4)
    with open(Path(OUTPUTS_LOGS_DIR) / "mlp_total_training_history.json", "w") as f:
        json.dump(mlp_total_history, f, indent=4)
    plot_training_loss(
        mlp_history,
        Path(OUTPUTS_PLOTS_DIR) / "mlp_training_loss.svg",
        title="MLP Training Loss (per-country)",
    )
    plot_training_loss(
        mlp_total_history,
        Path(OUTPUTS_PLOTS_DIR) / "mlp_total_training_loss.svg",
        title="MLP Training Loss (Total series)",
    )
    plot_model_comparison(
        total_results, Path(OUTPUTS_PLOTS_DIR) / "model_comparison.svg"
    )
    plot_model_comparison(
        per_country_results,
        Path(OUTPUTS_PLOTS_DIR) / "model_comparison_per_country.svg",
    )
    run_finished_at = datetime.now()
    _write_training_log(
        per_country_results,
        total_results,
        run_started_at,
        run_finished_at,
        data,
        total_data,
    )
    comparison = ModelComparison.compare(total_results)
    ModelComparison.save_comparison(comparison)
    ModelComparison.save_report(total_results)
    report_path = generate_html_report()
    print(f"HTML comparison report saved to: {report_path}")
    predict_total(save_to_disk=True)
    print("\nTraining completed successfully.")
    print(f"Models saved to: {SAVED_MODELS_DIR} and {SAVED_MODELS_TOTAL_DIR}")
    print(
        f"Diagnostics saved to: {OUTPUTS_LOGS_DIR}, {OUTPUTS_PLOTS_DIR}, {OUTPUTS_METRICS_DIR}, {OUTPUTS_FORECASTS_DIR}, and {OUTPUTS_REPORTS_DIR}"
    )


def _write_training_log(
    per_country_results, total_results, started_at, finished_at, data, total_data
) -> None:
    timestamp = started_at.strftime("%Y%m%d_%H%M%S")
    log_path = Path(OUTPUTS_LOGS_DIR) / f"train_run_{timestamp}.log"
    lines = [
        f"Training run: {started_at.isoformat()} -> {finished_at.isoformat()}",
        f"Duration: {(finished_at - started_at).total_seconds():.1f}s",
        f"Countries: {sorted(data.train_df['country'].unique())}",
        f"Per-country feature columns ({len(data.feature_columns)}): {data.feature_columns}",
        f"Total-series feature columns ({len(total_data.feature_columns)}): {total_data.feature_columns}",
        "",
        "Total-series results (primary -- this is what /predict serves):",
    ]
    for model_name, metrics in total_results.items():
        lines.append(
            f"  {model_name:<20} MAE={metrics['MAE']:.2f}  RMSE={metrics['RMSE']:.2f}  MAPE={metrics['MAPE']:.2f}%"
        )
    lines.append("")
    lines.append("Per-country results (averaged across 19 countries; reference only):")
    for model_name, metrics in per_country_results.items():
        lines.append(
            f"  {model_name:<20} MAE={metrics['MAE']:.2f}  RMSE={metrics['RMSE']:.2f}  MAPE={metrics['MAPE']:.2f}%"
        )
    log_path.write_text("\n".join(lines) + "\n")
    print(f"Training log written to: {log_path}")


if __name__ == "__main__":
    main()
