from __future__ import annotations

import logging
import os
import pickle

import numpy as np
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class LinearRegressionModel:
    def __init__(self):
        self.model = LinearRegression(fit_intercept=True)
        self.feature_names = None
        self.n_features = None
        self.is_fitted = False

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: list | None = None,
    ):
        self.feature_names = feature_names
        self.n_features = X_train.shape[1]
        logger.info(
            "Training Linear Regression (%d samples, %d features)",
            len(X_train),
            self.n_features,
        )
        self.model.fit(X_train, y_train.flatten())
        self.is_fitted = True
        logger.info("Linear Regression training completed.")
        if feature_names is not None:
            logger.info("Feature coefficients:")
            for name, coef in zip(feature_names, self.model.coef_):
                logger.info("%20s : %+10.4f", name, coef)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model has not been trained.")
        predictions = self.model.predict(X)
        return predictions.reshape(-1, 1)

    def save_model(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as file:
            pickle.dump(self, file)
        logger.info("Linear Regression model saved to %s", filepath)

    @classmethod
    def load_model(cls, filepath: str):
        with open(filepath, "rb") as file:
            model = pickle.load(file)
        logger.info("Linear Regression model loaded from %s", filepath)
        return model

    def save(self, filepath: str):
        self.save_model(filepath)

    @classmethod
    def load(cls, filepath: str):
        return cls.load_model(filepath)
