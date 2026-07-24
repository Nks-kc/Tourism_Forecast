"""
Retrain only Holt-Winters models (total + all countries).
Run with: python backend/retrain_hw.py
This is fast (~30s) and saves compatible .pkl files using statsmodels' own serialization.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from config import SAVED_MODELS_DIR, SAVED_MODELS_TOTAL_DIR
from feature_engineering.training_data import prepare_training_data
from feature_engineering.total_series import prepare_total_training_data
from models.holtwinters_model import HoltWintersModel
from evaluation.metrics import Metrics


def retrain_hw_per_country(data):
    print("\n── Per-country Holt-Winters ─────────────────────────────")
    save_dir = Path(SAVED_MODELS_DIR) / "holtwinters"
    save_dir.mkdir(parents=True, exist_ok=True)
    countries = sorted(data.train_df["country"].unique())
    metrics_list = []
    for country in countries:
        train_c = (
            data.train_df[data.train_df["country"] == country]
            .sort_values("date").reset_index(drop=True)
        )
        test_c = (
            data.test_df[data.test_df["country"] == country]
            .sort_values("date").reset_index(drop=True)
        )
        model = HoltWintersModel()
        model.fit(train_c[data.target_column].values)
        preds = model.predict(len(test_c))
        actual = test_c[data.target_column].values
        m = Metrics.evaluate(actual, preds)
        metrics_list.append(m)
        fname = country.replace(" ", "_") + ".pkl"
        model.save(str(save_dir / fname))
        print(f"  {country:<20} MAPE={m['MAPE']:.2f}%  saved → {fname}")
    avg = {
        "MAE": round(np.mean([m["MAE"] for m in metrics_list]), 2),
        "RMSE": round(np.mean([m["RMSE"] for m in metrics_list]), 2),
        "MAPE": round(np.mean([m["MAPE"] for m in metrics_list]), 2),
    }
    print(f"\n  Average → MAE={avg['MAE']}  RMSE={avg['RMSE']}  MAPE={avg['MAPE']}%")
    return avg


def retrain_hw_total(data):
    print("\n── Total-series Holt-Winters ────────────────────────────")
    Path(SAVED_MODELS_TOTAL_DIR).mkdir(parents=True, exist_ok=True)
    model = HoltWintersModel()
    model.fit(data.train_df[data.target_column].values)
    preds = model.predict(len(data.test_df))
    actual = data.test_df[data.target_column].values
    m = Metrics.evaluate(actual, preds)
    model.save(str(Path(SAVED_MODELS_TOTAL_DIR) / "holtwinters_total.pkl"))
    print(f"  MAE={m['MAE']}  RMSE={m['RMSE']}  MAPE={m['MAPE']}%")
    print("  Saved → holtwinters_total.pkl")
    return m


if __name__ == "__main__":
    print("=" * 56)
    print("Retraining Holt-Winters only (fast)")
    print("=" * 56)

    print("\nLoading per-country data...")
    data = prepare_training_data()
    retrain_hw_per_country(data)

    print("\nLoading total-series data...")
    total_data = prepare_total_training_data()
    retrain_hw_total(total_data)

    print("\n✓ Done. Call POST /admin/reload to clear server cache.")
