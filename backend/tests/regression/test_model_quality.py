"""
Regression tests: run after every `python train.py` to catch silent
degradation in model quality before it ships.
"""

import json
from pathlib import Path

import pytest

TOLERANCE = 1.15  # allow up to 15% worse than baseline before failing
METRICS = ["MAE", "RMSE", "MAPE"]

BACKEND_DIR = Path(__file__).resolve().parents[2]
REGRESSION_DIR = Path(__file__).resolve().parent


def _load(path):
    with open(path) as f:
        return json.load(f)


def _cases(latest_path, baseline_path, label):
    latest = _load(latest_path)
    baseline = _load(baseline_path)
    cases = []
    for model, baseline_metrics in baseline.items():
        for metric in METRICS:
            cases.append(
                pytest.param(
                    model,
                    metric,
                    latest.get(model, {}).get(metric),
                    baseline_metrics[metric],
                    id=f"{label}-{model}-{metric}",
                )
            )
    return cases


national_cases = _cases(
    BACKEND_DIR / "saved_models" / "results.json",
    REGRESSION_DIR / "baseline_results.json",
    "national",
)

country_cases = _cases(
    BACKEND_DIR / "saved_models" / "results_per_country.json",
    REGRESSION_DIR / "baseline_results_per_country.json",
    "country",
)


@pytest.mark.parametrize("model,metric,latest_value,baseline_value", national_cases)
def test_national_metric_within_tolerance(model, metric, latest_value, baseline_value):
    assert latest_value is not None, f"{model} is missing from the latest results.json"
    assert latest_value <= baseline_value * TOLERANCE, (
        f"{model} {metric} regressed: {latest_value} is more than "
        f"{int((TOLERANCE - 1) * 100)}% worse than baseline {baseline_value}"
    )


@pytest.mark.parametrize("model,metric,latest_value,baseline_value", country_cases)
def test_per_country_metric_within_tolerance(
    model, metric, latest_value, baseline_value
):
    assert latest_value is not None, (
        f"{model} is missing from the latest results_per_country.json"
    )
    assert latest_value <= baseline_value * TOLERANCE, (
        f"{model} {metric} regressed: {latest_value} is more than "
        f"{int((TOLERANCE - 1) * 100)}% worse than baseline {baseline_value}"
    )
