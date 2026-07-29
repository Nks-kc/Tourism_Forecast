import logging
import os
import warnings

import numpy as np
from config import SARIMA_ORDER, SARIMA_SEASONAL_ORDER
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class SARIMAModel:
    def __init__(self, order=SARIMA_ORDER, seasonal_order=SARIMA_SEASONAL_ORDER):
        self.order = order
        self.seasonal_order = seasonal_order
        self.result = None
        self.is_fitted = False

    def fit(self, y_train: np.ndarray, exog_train: np.ndarray | None = None):
        y = y_train.flatten()
        logger.info("Training SARIMA %s seasonal=%s", self.order, self.seasonal_order)
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

    def predict(self, steps: int, exog_future: np.ndarray | None = None) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model has not been trained.")
        forecast = self.result.forecast(steps=steps, exog=exog_future)
        return np.asarray(forecast)

    def save_model(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.result.save(filepath)
        logger.info("SARIMA model saved to %s", filepath)

    @classmethod
    def load_model(cls, filepath: str):
        model = cls()
        model.result = SARIMAXResults.load(filepath)
        model.is_fitted = True
        logger.info("SARIMA model loaded from %s", filepath)
        return model

    def save(self, filepath: str):
        self.save_model(filepath)

    @classmethod
    def load(cls, filepath: str):
        return cls.load_model(filepath)

