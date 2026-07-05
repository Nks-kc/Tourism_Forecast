"""
models/scaler.py

A lightweight NumPy implementation of StandardScaler.

This scaler standardizes features using:

    z = (x - mean) / std

It is primarily intended for the custom NumPy MLP.
"""

from __future__ import annotations

import numpy as np


class StandardScaler:
    """
    Standardize numerical features.
    """

    def __init__(self):

        self.mean_ = None
        self.std_ = None
        self.fitted = False

    def fit(self, X):
        """
        Compute mean and standard deviation.
        """

        X = np.asarray(X, dtype=np.float64)

        self.mean_ = np.mean(X, axis=0)

        self.std_ = np.std(X, axis=0)

        # Prevent division by zero
        self.std_[self.std_ == 0] = 1.0

        self.fitted = True

        return self

    def transform(self, X):
        """
        Standardize data.
        """

        if not self.fitted:
            raise RuntimeError(
                "Scaler has not been fitted."
            )

        X = np.asarray(X, dtype=np.float64)

        return (X - self.mean_) / self.std_

    def fit_transform(self, X):
        """
        Fit then transform.
        """

        self.fit(X)

        return self.transform(X)

    def inverse_transform(self, X):
        """
        Convert standardized values back to original scale.
        """

        if not self.fitted:
            raise RuntimeError(
                "Scaler has not been fitted."
            )

        X = np.asarray(X, dtype=np.float64)

        return (X * self.std_) + self.mean_

    def get_params(self):
        """
        Return scaler parameters.
        """

        return {
            "mean": self.mean_,
            "std": self.std_,
        }

    def set_params(self, mean, std):
        """
        Restore scaler parameters.
        """

        self.mean_ = np.asarray(mean)

        self.std_ = np.asarray(std)

        self.fitted = True