from __future__ import annotations

import logging

import pandas as pd
from data_store import load_country_arrivals
from feature_engineering.constants import COUNTRY_COLUMN, DATE_COLUMN
from feature_engineering.validators import validate_dataset

logger = logging.getLogger(__name__)


def load_data() -> pd.DataFrame:
    logger.info("Loading country-level dataset from the database...")
    df = load_country_arrivals()
    logger.info(
        "Dataset loaded successfully (%d rows, %d columns).", len(df), len(df.columns)
    )
    df = prepare_dataframe(df)
    validate_dataset(df)
    logger.info("Dataset validation successful.")
    return df


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Preparing dataframe...")
    df = df.copy()
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    df = df.sort_values(by=[COUNTRY_COLUMN, DATE_COLUMN]).reset_index(drop=True)
    logger.info("Dataframe prepared successfully.")
    return df
