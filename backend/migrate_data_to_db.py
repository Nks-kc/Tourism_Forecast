"""One-off CLI to load the seed CSVs into the database.

    python migrate_data_to_db.py

Run this once after cloning the repo (or after pulling this change) so the
app has data to serve. It's idempotent -- an upsert keyed on (date, country)
for country_arrivals and on date for national_arrivals -- so re-running it
is always safe and just re-syncs the DB with whatever the seed CSVs contain.

It reads two files and does NOT touch data/external/*.xlsx (that workbook is
only used at feature-engineering time, to cross-validate the country-level
data -- see feature_engineering/cross_validation.py):

    config.SEED_COUNTRY_CSV   -> country_arrivals table  (per-country model input)
    config.SEED_NATIONAL_CSV  -> national_arrivals table (nationwide model input)

After migrating, nothing at request-serving time reads these CSVs anymore --
feature_engineering/data_loader.py and feature_engineering/total_series.py
read from the database instead. The CSVs stay in the repo purely as the seed
source for this script (and for anyone who wants to inspect the raw numbers
directly).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from config import SEED_COUNTRY_CSV, SEED_NATIONAL_CSV
from data_store import (
    init_tourism_tables,
    upsert_country_arrivals,
    upsert_national_arrivals,
)


def _load_country_rows() -> list[dict]:
    path = Path(SEED_COUNTRY_CSV)
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df[["date", "country", "arrivals", "year", "month"]].to_dict("records")


def _load_national_rows() -> list[dict]:
    path = Path(SEED_NATIONAL_CSV)
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df = df.rename(columns={"foreign_arrivals": "arrivals"})
    return df[["date", "arrivals", "year", "month"]].to_dict("records")


def main():
    print("=" * 60)
    print("Migrating seed CSVs into the database")
    print("=" * 60)
    init_tourism_tables()

    print(f"\nReading country-level data from {SEED_COUNTRY_CSV}")
    country_rows = _load_country_rows()
    country_result = upsert_country_arrivals(country_rows)
    print(
        f"  country_arrivals: {country_result['added']} added, "
        f"{country_result['updated']} updated "
        f"({len(country_rows)} rows in source file)"
    )

    print(f"\nReading nationwide data from {SEED_NATIONAL_CSV}")
    national_rows = _load_national_rows()
    national_result = upsert_national_arrivals(national_rows)
    print(
        f"  national_arrivals: {national_result['added']} added, "
        f"{national_result['updated']} updated "
        f"({len(national_rows)} rows in source file)"
    )

    print("\nDone. The app now serves both datasets from the database.")


if __name__ == "__main__":
    main()
