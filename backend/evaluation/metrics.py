from __future__ import annotations

import json
from pathlib import Path

import numpy as np


class Metrics:
    @staticmethod
    def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        return float(np.mean(np.abs(y_true - y_pred)))

    @staticmethod
    def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    @staticmethod
    def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        mask = y_true != 0
        if not np.any(mask):
            return 0.0
        return float(
            np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        )

    @classmethod
    def evaluate(cls, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        return {
            "MAE": round(cls.mae(y_true, y_pred), 2),
            "RMSE": round(cls.rmse(y_true, y_pred), 2),
            "MAPE": round(cls.mape(y_true, y_pred), 2),
        }

    @staticmethod
    def print_results(results: dict) -> None:
        print("\n" + "=" * 60)
        print("Model Evaluation")
        print("=" * 60)
        print(f"{'Model':<22}{'MAE':>12}{'RMSE':>12}{'MAPE':>10}")
        print("-" * 60)
        for model, metrics in results.items():
            print(
                f"{model:<22}{metrics['MAE']:>12.2f}{metrics['RMSE']:>12.2f}{metrics['MAPE']:>9.2f}%"
            )

    @staticmethod
    def save_results(results: dict, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(results, f, indent=4)
