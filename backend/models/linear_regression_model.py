import os
import pickle
import numpy as np
from sklearn.linear_model import LinearRegression

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SAVED_MODELS_DIR


class LinearRegressionModel:

    def __init__(self):
        self.model         = None
        self.feature_names = None

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, feature_names: list = None):
        self.feature_names = feature_names
        print("  Fitting Linear Regression with Lag Features ...")
        print(f"  Training on {len(X_train)} samples, {X_train.shape[1]} features.")
        self.model = LinearRegression(fit_intercept=True)
        self.model.fit(X_train, y_train.flatten())
        print("  Linear Regression fitted successfully.")
        print(f"  Intercept: {self.model.intercept_:+.4f}")
        if feature_names is not None:
            print("  Learned feature coefficients:")
            for name, coef in zip(feature_names, self.model.coef_):
                bar  = "█" * min(int(abs(coef) * 5), 20)
                sign = "+" if coef >= 0 else "-"
                print(f"    {name:>16}:  {coef:+.4f}  {sign}{bar}")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Model not fitted. Call .fit() first.")
        return self.model.predict(X).reshape(-1, 1)

    def save(self, path: str):
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  Linear Regression saved → {path}")

    @classmethod
    def load(cls, path: str) -> "LinearRegressionModel":
        with open(path, "rb") as f:
            obj = pickle.load(f)
        print(f"  Linear Regression loaded ← {path}")
        return obj
