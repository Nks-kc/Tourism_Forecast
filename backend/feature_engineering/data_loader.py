from __future__ import annotations
import logging
from pathlib import Path
import pandas as pd
from config import RAW_DATA_FILE
from feature_engineering.constants import DATE_COLUMN, COUNTRY_COLUMN
from feature_engineering.validators import validate_dataset

logger = logging.getLogger(__name__)


def load_data(csv_path: str | Path | None = None) -> pd.DataFrame:
    path = Path(csv_path) if csv_path else Path(RAW_DATA_FILE)
    logger.info("Loading dataset from %s", path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found:\n{path}")
    df = pd.read_csv(path)
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
