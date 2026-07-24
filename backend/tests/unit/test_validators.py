# tests/unit/test_validators.py
import pandas as pd
import pytest
from feature_engineering.validators import validate_dataset, validate_negative_values


def test_negative_arrivals_flagged():
    df = pd.DataFrame({"arrivals": [-5, 10]})
    assert len(validate_negative_values(df)) == 1


def test_validate_dataset_raises_on_missing_columns():
    with pytest.raises(ValueError):
        validate_dataset(pd.DataFrame({"foo": [1]}))

def test_missing_only_arrivals_column_raises_cleanly():
    df = pd.DataFrame(
        {"date": ["2020-01-01"], "year": [2020], "month": [1], "country": ["Nepal"]}
    )
    with pytest.raises(ValueError):
        validate_dataset(df)


def test_missing_only_date_column_raises_cleanly():
    df = pd.DataFrame(
        {"year": [2020], "month": [1], "country": ["Nepal"], "arrivals": [100]}
    )
    with pytest.raises(ValueError):
        validate_dataset(df)