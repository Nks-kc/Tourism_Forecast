"""
models/sarima_model.py
----------------------
SARIMA (Seasonal ARIMA) — imported from statsmodels, NOT implemented from scratch.
This is the strongest baseline comparison model for the MLP.

WHAT SARIMA DOES (plain English):
  It looks at the history of tourist arrivals and finds three patterns:
    AR (AutoRegression):  "Last month's tourists predict this month's."
    I  (Integrated):      "Let's look at the change in tourists, not the raw number."
    MA (Moving Average):  "Last month's forecast error can predict this month too."
    S  (Seasonal):        All of the above, but for 12-month cycles.

  We use SARIMAX (the X = exogenous variables), meaning we can also feed in
  external features like trekking season flags and the COVID dummy variable.

WHY KEEP THIS ALONGSIDE MLP?
  - SARIMA is interpretable: you can see exact coefficients.
  - It's a proven industry standard for seasonal time series.
  - Comparing MLP vs SARIMA tells you how much value the neural network adds.
"""

import logging
import os
import warnings

import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults

from config import SARIMA_ORDER, SARIMA_SEASONAL_ORDER

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class SARIMAModel:
    """
    Wrapper around statsmodels' SARIMAX implementation.
    """

    def __init__(
        self,
        order=SARIMA_ORDER,
        seasonal_order=SARIMA_SEASONAL_ORDER,
    ):

        self.order = order
        self.seasonal_order = seasonal_order

        self.result = None

        self.is_fitted = False

    def fit(
        self,
        y_train: np.ndarray,
        exog_train: np.ndarray | None = None,
    ):
        """
        Train the SARIMA model.
        """

        y = y_train.flatten()

        logger.info(
            "Training SARIMA %s seasonal=%s",
            self.order,
            self.seasonal_order,
        )

        model = SARIMAX(
            y,
            exog=exog_train,
            order=self.order,
            seasonal_order=self.seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )

        self.result = model.fit(disp=False)

        self.is_fitted = True

        logger.info("SARIMA training completed.")

        return self

    def predict(
        self,
        steps: int,
        exog_future: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Forecast future values.
        """

        if not self.is_fitted:
            raise RuntimeError("Model has not been trained.")

        forecast = self.result.forecast(
            steps=steps,
            exog=exog_future,
        )

        return np.asarray(forecast)

    def save_model(
        self,
        filepath: str,
    ):
        """
        Save the trained SARIMA model.
        """

        os.makedirs(
            os.path.dirname(filepath),
            exist_ok=True,
        )

        self.result.save(filepath)

        logger.info(
            "SARIMA model saved to %s",
            filepath,
        )

    @classmethod
    def load_model(
        cls,
        filepath: str,
    ):
        """
        Load a trained SARIMA model.
        """

        model = cls()

        model.result = SARIMAXResults.load(filepath)

        model.is_fitted = True

        logger.info(
            "SARIMA model loaded from %s",
            filepath,
        )

        return model

    # ----------------------------------------------------
    # Backward compatibility
    # ----------------------------------------------------

    def save(self, filepath: str):
        self.save_model(filepath)

    @classmethod
    def load(cls, filepath: str):
        return cls.load_model(filepath)

