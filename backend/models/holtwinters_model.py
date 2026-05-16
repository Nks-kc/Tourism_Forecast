"""
models/holtwinters_model.py
----------------------------
Holt-Winters Exponential Smoothing — imported from statsmodels.

WHAT HOLT-WINTERS DOES (plain English):
  It splits the time series into three components and tracks each separately:
    Level:   The "current average" — updated each month.
    Trend:   Is tourism growing or shrinking over time?
    Season:  A 12-month repeating pattern (high in trekking seasons, low in monsoon).

  Each component uses "exponential smoothing" — recent data matters more
  than old data, with older data weighted exponentially less.

LIMITATIONS (why it is the weakest of our three models):
  - Cannot accept external variables (no trekking flags, no COVID dummy).
  - Assumes the seasonal pattern doesn't change shape over time.
  - Works best on stable, regular series — less good for post-COVID recovery.

WHY INCLUDE IT ANYWAY?
  - It is very fast (< 1 second to train).
  - It provides a second baseline alongside SARIMA.
  - If MLP beats both baselines, that is compelling evidence for your project.
"""

import os
import pickle
import warnings
import numpy as np

warnings.filterwarnings("ignore")

from statsmodels.tsa.holtwinters import ExponentialSmoothing

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import HW_TREND, HW_SEASONAL, HW_SEASONAL_PERIODS, SAVED_MODELS_DIR


class HoltWintersModel:

    def __init__(self, trend=HW_TREND, seasonal=HW_SEASONAL,
                 seasonal_periods=HW_SEASONAL_PERIODS):
        """
        Args:
            trend:            "add" = additive (seasonality stays same size over time)
                              "mul" = multiplicative (seasonality grows with the level)
                              Use "add" when you are unsure — it is more stable.
            seasonal:         Same "add" / "mul" choice for the seasonal component.
            seasonal_periods: 12 for monthly data (one full cycle = 12 months)
        """
        self.trend            = trend
        self.seasonal         = seasonal
        self.seasonal_periods = seasonal_periods
        self.model            = None  # will hold the fitted model after .fit()

    def fit(self, y_train: np.ndarray):
        """
        Fit Holt-Winters on training data.

        Args:
            y_train: Monthly tourist arrivals, shape (n,) or (n,1)
                     Needs at least 2 × seasonal_periods = 24 months of data.
        """
        y = y_train.flatten()

        print(f"  Fitting Holt-Winters (trend='{self.trend}', seasonal='{self.seasonal}') ...")
        print(f"  Training on {len(y)} months of data.")

        hw = ExponentialSmoothing(
            y,
            trend            = self.trend,
            seasonal         = self.seasonal,
            seasonal_periods = self.seasonal_periods,
        )
        # optimized=True: statsmodels finds the best smoothing parameters automatically
        self.model = hw.fit(optimized=True)
        print("  Holt-Winters fitted successfully.")

    def predict(self, steps: int) -> np.ndarray:
        """
        Forecast tourist arrivals for the next `steps` months.

        Args:
            steps: Number of months to forecast (1, 3, 6, or 12)

        Returns:
            Predicted arrivals array, shape (steps,)
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call .fit() first.")

        return np.array(self.model.forecast(steps))

    def save(self, path: str):
        """Save the fitted model using pickle."""
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.model, f)
        print(f"  Holt-Winters saved → {path}")

    def load(self, path: str):
        """Load a previously saved Holt-Winters model."""
        with open(path, "rb") as f:
            self.model = pickle.load(f)
        print(f"  Holt-Winters loaded ← {path}")
