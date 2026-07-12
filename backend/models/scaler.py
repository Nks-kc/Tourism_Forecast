from __future__ import annotations
import numpy as np


class StandardScaler:
    def __init__(self):
        self.mean_ = None
        self.std_ = None
        self.fitted = False

    def fit(self, X):
        X = np.asarray(X, dtype=np.float64)
        self.mean_ = np.mean(X, axis=0)
        self.std_ = np.std(X, axis=0)
        self.std_[self.std_ == 0] = 1.0
        self.fitted = True
        return self

    def transform(self, X):
        if not self.fitted:
            raise RuntimeError("Scaler has not been fitted.")
        X = np.asarray(X, dtype=np.float64)
        return (X - self.mean_) / self.std_

    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X):
        if not self.fitted:
            raise RuntimeError("Scaler has not been fitted.")
        X = np.asarray(X, dtype=np.float64)
        return X * self.std_ + self.mean_

    def get_params(self):
        return {"mean": self.mean_, "std": self.std_}

    def set_params(self, mean, std):
        self.mean_ = np.asarray(mean)
        self.std_ = np.asarray(std)
        self.fitted = True
