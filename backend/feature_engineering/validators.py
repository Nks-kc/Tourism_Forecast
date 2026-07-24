from __future__ import annotations
import logging
from typing import List
import pandas as pd
from feature_engineering.constants import (
    REQUIRED_COLUMNS,
    DATE_COLUMN,
    COUNTRY_COLUMN,
    TARGET_COLUMN,
    MIN_ARRIVALS,
)

logger = logging.getLogger(__name__)


def validate_dataset(df: pd.DataFrame) -> None:
    logger.info("Validating dataset...")
    errors = []
    errors.extend(validate_required_columns(df))
    if errors:
        message = "\n".join(errors)
        logger.error(message)
        raise ValueError(message)  

    errors.extend(validate_duplicate_rows(df))
    errors.extend(validate_negative_values(df))
    errors.extend(validate_missing_values(df))
    errors.extend(validate_invalid_dates(df))
    errors.extend(validate_country_names(df))
    errors.extend(validate_monthly_sequence(df))
    if errors:
        message = "\n".join(errors)
        logger.error(message)
        raise ValueError(message)
    logger.info("Dataset validation completed successfully.")


def validate_required_columns(df: pd.DataFrame) -> List[str]:
    errors = []
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")
    return errors


def validate_duplicate_rows(df: pd.DataFrame) -> List[str]:
    errors = []
    duplicates = df.duplicated(subset=[COUNTRY_COLUMN, DATE_COLUMN])
    if duplicates.any():
        count = duplicates.sum()
        errors.append(f"Found {count} duplicate country/date rows.")
    return errors


def validate_negative_values(df: pd.DataFrame) -> List[str]:
    errors = []
    negative = df[TARGET_COLUMN] < MIN_ARRIVALS
    if negative.any():
        count = negative.sum()
        errors.append(f"Found {count} negative arrival values.")
    return errors


def validate_missing_values(df: pd.DataFrame) -> List[str]:
    errors = []
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing):
        for column, value in missing.items():
            errors.append(f"Column '{column}' contains {value} missing values.")
    return errors


def validate_invalid_dates(df: pd.DataFrame) -> List[str]:
    errors = []
    try:
        pd.to_datetime(df[DATE_COLUMN])
    except Exception:
        errors.append("Date column contains invalid values.")
    return errors


def validate_country_names(df: pd.DataFrame) -> List[str]:
    errors = []
    countries = df[COUNTRY_COLUMN].astype(str).str.strip()
    invalid = countries == ""
    if invalid.any():
        errors.append("Dataset contains empty country names.")
    return errors


def validate_monthly_sequence(df: pd.DataFrame) -> List[str]:
    errors = []
    grouped = df.groupby(COUNTRY_COLUMN)
    for country, group in grouped:
        group = group.sort_values(DATE_COLUMN)
        expected = pd.date_range(
            start=group[DATE_COLUMN].min(), end=group[DATE_COLUMN].max(), freq="MS"
        )
        actual = pd.DatetimeIndex(group[DATE_COLUMN])
        missing = expected.difference(actual)
        if len(missing):
            errors.append(f"{country}: {len(missing)} missing month(s).")
    return errors
