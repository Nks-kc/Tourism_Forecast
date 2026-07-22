# tests/unit/test_metrics.py
from evaluation.metrics import Metrics


def test_mae_known_value():
    assert Metrics.mae([100, 200], [110, 190]) == 10.0


def test_rmse_known_value():
    assert Metrics.rmse([0, 0], [3, 4]) == 3.5355339059327378


def test_mape_ignores_zero_actuals():
    # zero actuals must be masked out, not divide-by-zero
    assert Metrics.mape([0, 100], [50, 110]) == 10.0
