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

import os
import warnings
import numpy as np

warnings.filterwarnings("ignore")

from statsmodels.tsa.statespace.sarimax import SARIMAX

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SARIMA_ORDER, SARIMA_SEASONAL_ORDER, SAVED_MODELS_DIR


class SARIMAModel:

    def __init__(self, order=SARIMA_ORDER, seasonal_order=SARIMA_SEASONAL_ORDER):
        """
        Args:
            order:          (p, d, q)
                              p = AR order: how many past values to use
                              d = differencing: 1 usually makes series stationary
                              q = MA order: how many past errors to use
            seasonal_order: (P, D, Q, s)
                              Same as above but for seasonal cycles.
                              s = 12 because we have monthly data.
        """
        self.order          = order
        self.seasonal_order = seasonal_order
        self.result         = None  # will hold the fitted model after .fit()

    def fit(self, y_train: np.ndarray, exog_train: np.ndarray = None):
        """
        Fit the SARIMA model on training data.

        Args:
            y_train:    Monthly tourist arrivals, shape (n,) or (n,1)
            exog_train: Optional external features, shape (n, n_features)
                        e.g. [[is_spring_trek, is_autumn_trek, is_monsoon, is_covid], ...]
        """
        y = y_train.flatten()

        print(f"  Fitting SARIMA order={self.order}, seasonal={self.seasonal_order} ...")
        print(f"  Training on {len(y)} months of data.")

        model = SARIMAX(
            y,
            exog                  = exog_train,
            order                 = self.order,
            seasonal_order        = self.seasonal_order,
            enforce_stationarity  = False,   # avoids errors on some datasets
            enforce_invertibility = False,
        )
        self.result = model.fit(disp=False)  # disp=False suppresses verbose output

        print("  SARIMA fitted successfully.")
        # Print a short summary of the fit
        print(self.result.summary().tables[0].as_text())

    def predict(self, steps: int, exog_future: np.ndarray = None) -> np.ndarray:
        """
        Forecast tourist arrivals for the next `steps` months.

        Args:
            steps:        Number of months to forecast (1, 3, 6, or 12)
            exog_future:  External features for future months, shape (steps, n_features)
                          Must be provided if exog_train was used during fit().

        Returns:
            Predicted arrivals array, shape (steps,)
        """
        if self.result is None:
            raise RuntimeError("Model not fitted. Call .fit() first.")

        forecast = self.result.forecast(steps=steps, exog=exog_future)
        return np.array(forecast)

    def save(self, path: str):
        """Save using statsmodels' native .save() — avoids Windows errno 22 on large pickle writes."""
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        self.result.save(path)
        print(f"  SARIMA saved → {path}")

    def load(self, path: str):
        """Load a previously saved SARIMA result object."""
        from statsmodels.tsa.statespace.sarimax import SARIMAXResults
        self.result = SARIMAXResults.load(path)
        print(f"  SARIMA loaded ← {path}")

