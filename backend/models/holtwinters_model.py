import logging
import os
import pickle
import warnings
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from config import HW_TREND, HW_SEASONAL, HW_SEASONAL_PERIODS

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class HoltWintersModel:
    def __init__(
        self, trend=HW_TREND, seasonal=HW_SEASONAL, seasonal_periods=HW_SEASONAL_PERIODS
    ):
        self.trend = trend
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods
        self.model = None
        self.is_fitted = False

    def fit(self, y_train: np.ndarray):
        y = y_train.flatten()
        logger.info(
            "Training Holt-Winters (trend=%s, seasonal=%s)", self.trend, self.seasonal
        )
        hw = ExponentialSmoothing(
            y,
            trend=self.trend,
            seasonal=self.seasonal,
            seasonal_periods=self.seasonal_periods,
        )
        self.model = hw.fit(optimized=True)
        self.is_fitted = True
        logger.info("Holt-Winters training completed.")
        return self

    def predict(self, steps: int) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model has not been trained.")
        forecast = self.model.forecast(steps)
        return np.asarray(forecast)

    def save_model(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as file:
            pickle.dump(self.model, file)
        logger.info("Holt-Winters model saved to %s", filepath)

    @classmethod
    def load_model(cls, filepath: str):
        with open(filepath, "rb") as file:
            fitted_model = pickle.load(file)
        model = cls()
        model.model = fitted_model
        model.is_fitted = True
        logger.info("Holt-Winters model loaded from %s", filepath)
        return model

    def save(self, filepath: str):
        self.save_model(filepath)

    @classmethod
    def load(cls, filepath: str):
        return cls.load_model(filepath)
