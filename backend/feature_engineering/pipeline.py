from __future__ import annotations
import logging
from pathlib import Path
from config import PROCESSED_CSV
from feature_engineering.cross_validation import run_cross_validation
from feature_engineering.preprocessing import preprocess_data
from feature_engineering.features import (
    add_time_features, 
    add_rolling_features, 
    remove_initial_rolling_rows,
    add_lag_features,
    remove_initial_nan_rows
)
from feature_engineering.encoding import encode_country

logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("=" * 60)
    logger.info("Starting Feature Engineering Pipeline")
    logger.info("=" * 60)
    df = run_cross_validation()
    logger.info("Loaded and cross-validated dataset.")
    df = preprocess_data(df)
    logger.info("Preprocessing complete.")
    df = add_time_features(df)
    logger.info("Time features added.")
    df = add_lag_features(df)
    logger.info("Lag features added.")
    df = add_rolling_features(df)
    logger.info("Rolling features added.")
    df = remove_initial_nan_rows(df)
    df = remove_initial_rolling_rows(df)
    logger.info("Removed initialization rows.")
    df = encode_country(df)
    logger.info("Country encoding complete.")
    output_path = Path(PROCESSED_CSV)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Processed dataset saved to %s", output_path)
    logger.info("=" * 60)
    logger.info("Pipeline Completed Successfully")
    logger.info("=" * 60)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    run_pipeline()
