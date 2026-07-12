from __future__ import annotations
import logging
import pandas as pd
from feature_engineering.constants import (
    DATE_COLUMN,
    YEAR_COLUMN,
    MONTH_COLUMN,
    COUNTRY_COLUMN,
    TARGET_COLUMN,
)

logger = logging.getLogger(__name__)


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting preprocessing...")
    df = df.copy()
    df = standardize_country_names(df)
    df = rebuild_date_columns(df)
    df = convert_data_types(df)
    df = remove_duplicates(df)
    df = sort_dataframe(df)
    logger.info("Preprocessing completed.")
    return df


def standardize_country_names(df: pd.DataFrame) -> pd.DataFrame:
    df[COUNTRY_COLUMN] = df[COUNTRY_COLUMN].astype(str).str.strip()
    return df


def rebuild_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    df[YEAR_COLUMN] = df[DATE_COLUMN].dt.year
    df[MONTH_COLUMN] = df[DATE_COLUMN].dt.month
    return df


def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    df[YEAR_COLUMN] = df[YEAR_COLUMN].astype(int)
    df[MONTH_COLUMN] = df[MONTH_COLUMN].astype(int)
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(float)
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=[COUNTRY_COLUMN, DATE_COLUMN])
    removed = before - len(df)
    if removed:
        logger.warning("Removed %d duplicate rows.", removed)
    return df


def sort_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(by=[COUNTRY_COLUMN, DATE_COLUMN]).reset_index(drop=True)
