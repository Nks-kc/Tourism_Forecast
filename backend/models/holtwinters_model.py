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

import logging
import os
import pickle
import warnings

import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from config import (
    HW_TREND,
    HW_SEASONAL,
    HW_SEASONAL_PERIODS,
)

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class HoltWintersModel:
    """
    Wrapper around statsmodels' Holt-Winters implementation.
    """

    def __init__(
        self,
        trend=HW_TREND,
        seasonal=HW_SEASONAL,
        seasonal_periods=HW_SEASONAL_PERIODS,
    ):

        self.trend = trend
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods

        self.model = None

        self.is_fitted = False

    def fit(
        self,
        y_train: np.ndarray,
    ):
        """
        Train the Holt-Winters model.
        """

        y = y_train.flatten()

        logger.info(
            "Training Holt-Winters (trend=%s, seasonal=%s)",
            self.trend,
            self.seasonal,
        )

        hw = ExponentialSmoothing(
            y,
            trend=self.trend,
            seasonal=self.seasonal,
            seasonal_periods=self.seasonal_periods,
        )

        self.model = hw.fit(
            optimized=True,
        )

        self.is_fitted = True

        logger.info("Holt-Winters training completed.")

        return self

    def predict(
        self,
        steps: int,
    ) -> np.ndarray:
        """
        Forecast future observations.
        """

        if not self.is_fitted:
            raise RuntimeError("Model has not been trained.")

        forecast = self.model.forecast(
            steps,
        )

        return np.asarray(forecast)

    def save_model(
        self,
        filepath: str,
    ):
        """
        Save the trained Holt-Winters model.
        """

        os.makedirs(
            os.path.dirname(filepath),
            exist_ok=True,
        )

        with open(filepath, "wb") as file:
            pickle.dump(
                self.model,
                file,
            )

        logger.info(
            "Holt-Winters model saved to %s",
            filepath,
        )

    @classmethod
    def load_model(
        cls,
        filepath: str,
    ):
        """
        Load a trained Holt-Winters model.
        """

        with open(filepath, "rb") as file:
            fitted_model = pickle.load(file)

        model = cls()

        model.model = fitted_model

        model.is_fitted = True

        logger.info(
            "Holt-Winters model loaded from %s",
            filepath,
        )

        return model

    # --------------------------------------------------------
    # Backward compatibility
    # --------------------------------------------------------

    def save(self, filepath: str):
        self.save_model(filepath)

    @classmethod
    def load(cls, filepath: str):
        return cls.load_model(filepath)
