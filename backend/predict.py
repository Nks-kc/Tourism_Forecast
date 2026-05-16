import os
import argparse
import numpy as np
import pandas as pd

from models.mlp                     import MLP
from models.sarima_model            import SARIMAModel
from models.holtwinters_model       import HoltWintersModel
from models.linear_regression_model import LinearRegressionModel
from utils.feature_engineering      import add_features
from config import PROCESSED_CSV, SAVED_MODELS_DIR, FEATURE_COLS, LR_MODEL_FILENAME


def load_scalers() -> dict:
    path = os.path.join(SAVED_MODELS_DIR, "scalers.npz")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Scalers not found at {path}\nRun 'python train.py' first.")
    data = np.load(path)
    return {
        "feat": {"mean": data["feat_mean"], "std": data["feat_std"]},
        "tgt":  {"mean": float(data["tgt_mean"][0]), "std": float(data["tgt_std"][0])},
    }


def build_future_features(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    last_date        = df["date"].max()
    arrivals_history = df["foreign_arrivals"].tolist()
    year_min, year_max = df["year"].min(), df["year"].max()
    future_rows = []

    for i in range(1, horizon + 1):
        future_date = last_date + pd.DateOffset(months=i)
        month, year = future_date.month, future_date.year
        denom       = max(max(year_max, year) - year_min, 1)
        row = {
            "date": future_date, "year": year, "month": month,
            "month_sin":      float(np.sin(2 * np.pi * month / 12)),
            "month_cos":      float(np.cos(2 * np.pi * month / 12)),
            "year_norm":      (year - year_min) / denom,
            "is_spring_trek": int(month in [3, 4, 5]),
            "is_autumn_trek": int(month in [9, 10, 11]),
            "is_monsoon":     int(month in [6, 7, 8]),
            "is_covid":       0,
            "lag_1":          arrivals_history[-1]  if len(arrivals_history) >= 1  else 0.0,
            "lag_3":          arrivals_history[-3]  if len(arrivals_history) >= 3  else 0.0,
            "lag_12":         arrivals_history[-12] if len(arrivals_history) >= 12 else 0.0,
        }
        future_rows.append(row)
        arrivals_history.append(arrivals_history[-1])

    return pd.DataFrame(future_rows)


def predict_all(horizon: int) -> dict:
    df           = pd.read_csv(PROCESSED_CSV, parse_dates=["date"])
    df           = add_features(df)
    scalers      = load_scalers()
    future_df    = build_future_features(df, horizon)
    future_dates = future_df["date"].dt.strftime("%Y-%m").tolist()
    predictions  = {}

    mlp_path = os.path.join(SAVED_MODELS_DIR, "mlp.npz")
    if os.path.exists(mlp_path):
        try:
            mlp         = MLP.load(mlp_path)
            X_future    = future_df[FEATURE_COLS].values
            X_future_sc = (X_future - scalers["feat"]["mean"]) / scalers["feat"]["std"]
            y_sc        = mlp.predict(X_future_sc).flatten()
            y_raw       = y_sc * scalers["tgt"]["std"] + scalers["tgt"]["mean"]
            predictions["MLP"] = {"months": future_dates, "arrivals": [max(0, round(float(v))) for v in y_raw]}
        except Exception as e:
            print(f"  Skipping MLP prediction: {e}")

    sarima_path = os.path.join(SAVED_MODELS_DIR, "sarima.pkl")
    if os.path.exists(sarima_path):
        try:
            sarima = SARIMAModel()
            sarima.load(sarima_path)
            exog_future = future_df[["is_spring_trek", "is_autumn_trek", "is_monsoon", "is_covid"]].values
            y_raw = sarima.predict(steps=horizon, exog_future=exog_future)
            predictions["SARIMA"] = {"months": future_dates, "arrivals": [max(0, round(float(v))) for v in y_raw]}
        except Exception as e:
            print(f"  Skipping SARIMA prediction: {e}")

    hw_path = os.path.join(SAVED_MODELS_DIR, "holtwinters.pkl")
    if os.path.exists(hw_path):
        try:
            hw    = HoltWintersModel()
            hw.load(hw_path)
            y_raw = hw.predict(steps=horizon)
            predictions["Holt-Winters"] = {"months": future_dates, "arrivals": [max(0, round(float(v))) for v in y_raw]}
        except Exception as e:
            print(f"  Skipping Holt-Winters prediction: {e}")

    lr_path = os.path.join(SAVED_MODELS_DIR, LR_MODEL_FILENAME)
    if os.path.exists(lr_path):
        try:
            lr          = LinearRegressionModel.load(lr_path)
            X_future    = future_df[FEATURE_COLS].values
            X_future_sc = (X_future - scalers["feat"]["mean"]) / scalers["feat"]["std"]
            y_sc        = lr.predict(X_future_sc).flatten()
            y_raw       = y_sc * scalers["tgt"]["std"] + scalers["tgt"]["mean"]
            predictions["Linear Regression"] = {"months": future_dates, "arrivals": [max(0, round(float(v))) for v in y_raw]}
        except Exception as e:
            print(f"  Skipping Linear Regression prediction: {e}")

    if not predictions:
        raise RuntimeError("No saved models could generate predictions. Re-run 'python train.py'.")

    return predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nepal Tourism Forecast")
    parser.add_argument("--horizon", type=int, choices=[1, 3, 6, 12], default=3)
    args = parser.parse_args()
    print(f"\nGenerating {args.horizon}-month forecast...\n")
    preds = predict_all(args.horizon)
    for model_name, result in preds.items():
        print(f"\n  {model_name}:")
        for month, arrivals in zip(result["months"], result["arrivals"]):
            print(f"    {month}:  {arrivals:>10,} tourists")
