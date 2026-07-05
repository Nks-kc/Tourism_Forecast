"""
feature_engineering/pipeline.py

Runs the complete feature engineering pipeline.

Pipeline Steps
--------------
1. Load raw dataset
2. Validate dataset
3. Preprocess dataset
4. Generate time features
5. Generate lag features
6. Generate rolling features
7. Remove initialization rows
8. One-hot encode countries
9. Save processed dataset

Author: Tourism Forecasting Project
"""

from __future__ import annotations

import logging
from pathlib import Path

from config import (
    PROCESSED_CSV,
)

from feature_engineering.data_loader import load_data
from feature_engineering.preprocessing import preprocess_data
from feature_engineering.time_features import add_time_features
from feature_engineering.lag_features import (
    add_lag_features,
    remove_initial_nan_rows,
)
from feature_engineering.rolling_features import (
    add_rolling_features,
    remove_initial_rolling_rows,
)
from feature_engineering.encoding import encode_country

logger = logging.getLogger(__name__)


def run_pipeline():
    """
    Execute the complete feature engineering pipeline.
    """

    logger.info("=" * 60)
    logger.info("Starting Feature Engineering Pipeline")
    logger.info("=" * 60)

    df = load_data()

    logger.info("Loaded dataset.")

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

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        output_path,
        index=False,
    )

    logger.info(
        "Processed dataset saved to %s",
        output_path,
    )

    logger.info("=" * 60)
    logger.info("Pipeline Completed Successfully")
    logger.info("=" * 60)

    return df


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s",
    )

    run_pipeline()