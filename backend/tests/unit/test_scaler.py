# tests/unit/test_scaler.py
import numpy as np
from models.scaler import StandardScaler


def test_fit_transform_zero_mean_unit_std():
    X = np.array([[1.0], [2.0], [3.0]])
    scaled = StandardScaler().fit_transform(X)
    assert np.isclose(scaled.mean(), 0.0)


def test_constant_column_does_not_divide_by_zero():
    X = np.array([[5.0], [5.0], [5.0]])  # std == 0
    scaled = StandardScaler().fit_transform(X)
    assert np.all(np.isfinite(scaled))  # std_ is clamped to 1.0


def test_transform_before_fit_raises():
    import pytest

    with pytest.raises(RuntimeError):
        StandardScaler().transform([[1.0]])


def test_inverse_transform_recovers_original():
    X = np.array([[10.0], [20.0], [30.0]])
    s = StandardScaler().fit(X)
    assert np.allclose(s.inverse_transform(s.transform(X)), X)
