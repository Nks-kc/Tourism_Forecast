from __future__ import annotations
from functools import lru_cache
import pandas as pd
from config import PROCESSED_CSV
from feature_engineering.constants import (
    DATE_COLUMN,
    YEAR_COLUMN,
    MONTH_COLUMN,
    TARGET_COLUMN,
    COUNTRY_COLUMN,
)

EXCLUDED_COLUMNS = {
    DATE_COLUMN,
    YEAR_COLUMN,
    MONTH_COLUMN,
    TARGET_COLUMN,
    COUNTRY_COLUMN,
}


@lru_cache(maxsize=1)
def _read_processed_csv() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_CSV)


def load_processed_dataset() -> pd.DataFrame:
    return _read_processed_csv().copy()


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in df.columns if column not in EXCLUDED_COLUMNS]


def get_target_column() -> str:
    return TARGET_COLUMN


def get_available_countries() -> list[str]:
    df = load_processed_dataset()
    country_columns = [column for column in df.columns if column.startswith("country_")]
    countries = (
        pd.Series(country_columns)
        .str.replace("country_", "", regex=False)
        .sort_values()
        .tolist()
    )
    return countries
