from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
from config import RAW_DATA_FILE
from feature_engineering.constants import (
    COUNTRY_COLUMN,
    DATE_COLUMN,
    MONTH_COLUMN,
    TARGET_COLUMN,
    YEAR_COLUMN,
)


class DataIngestionError(ValueError):
    """Raised when submitted monthly data fails validation."""


def _normalize_entry(entry: dict, default_year, default_month) -> dict:
    country = str(entry.get("country", "")).strip()
    if not country:
        raise DataIngestionError("Each entry must include a non-empty 'country'.")

    if "arrivals" not in entry:
        raise DataIngestionError(f"Entry for '{country}' is missing 'arrivals'.")
    try:
        arrivals = int(entry["arrivals"])
    except (TypeError, ValueError):
        raise DataIngestionError(f"'arrivals' for '{country}' must be an integer.")
    if arrivals < 0:
        raise DataIngestionError(f"'arrivals' for '{country}' cannot be negative.")

    date_str = entry.get("date")
    if date_str:
        try:
            date = pd.to_datetime(date_str).replace(day=1)
        except Exception:  # noqa: BLE001
            raise DataIngestionError(f"Invalid date '{date_str}' for '{country}'.")
    else:
        year = entry.get("year", default_year)
        month = entry.get("month", default_month)
        if year is None or month is None:
            raise DataIngestionError(
                f"Entry for '{country}' needs a 'date' or a top-level 'year'/'month'."
            )
        try:
            date = pd.Timestamp(year=int(year), month=int(month), day=1)
        except Exception:  # noqa: BLE001
            raise DataIngestionError(f"Invalid year/month for '{country}'.")

    return {
        DATE_COLUMN: date,
        COUNTRY_COLUMN: country,
        TARGET_COLUMN: arrivals,
        YEAR_COLUMN: date.year,
        MONTH_COLUMN: date.month,
    }


def append_monthly_data(
    entries: list[dict],
    year: int | None = None,
    month: int | None = None,
    overwrite: bool = True,
) -> dict:
    """
    Add or update one or more country/month arrival records in the raw dataset.

    Each entry needs 'country' and 'arrivals', plus either its own 'date'
    (YYYY-MM-DD) or it will fall back to the shared top-level year/month.
    Existing (country, month) rows are updated in place when overwrite=True;
    otherwise a duplicate raises DataIngestionError.
    """
    if not entries:
        raise DataIngestionError("No entries provided.")

    new_rows = [_normalize_entry(e, year, month) for e in entries]
    new_df = pd.DataFrame(new_rows)

    raw_path = Path(RAW_DATA_FILE)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}")

    existing_df = pd.read_csv(raw_path)
    existing_df[DATE_COLUMN] = pd.to_datetime(existing_df[DATE_COLUMN])

    added, updated = [], []
    for _, row in new_df.iterrows():
        mask = (existing_df[COUNTRY_COLUMN] == row[COUNTRY_COLUMN]) & (
            existing_df[DATE_COLUMN] == row[DATE_COLUMN]
        )
        label = f"{row[COUNTRY_COLUMN]} ({row[DATE_COLUMN].strftime('%Y-%m')})"
        if mask.any():
            if not overwrite:
                raise DataIngestionError(f"Data for {label} already exists.")
            existing_df.loc[mask, TARGET_COLUMN] = row[TARGET_COLUMN]
            updated.append(label)
        else:
            existing_df = pd.concat([existing_df, row.to_frame().T], ignore_index=True)
            added.append(label)

    existing_df[DATE_COLUMN] = pd.to_datetime(existing_df[DATE_COLUMN])
    existing_df = existing_df.sort_values([COUNTRY_COLUMN, DATE_COLUMN]).reset_index(
        drop=True
    )
    existing_df[YEAR_COLUMN] = existing_df[DATE_COLUMN].dt.year
    existing_df[MONTH_COLUMN] = existing_df[DATE_COLUMN].dt.month
    existing_df[DATE_COLUMN] = existing_df[DATE_COLUMN].dt.strftime("%Y-%m-%d")

    # Atomic write so a crash mid-write can't corrupt the dataset
    fd, tmp_path = tempfile.mkstemp(dir=raw_path.parent, suffix=".csv")
    os.close(fd)
    existing_df.to_csv(tmp_path, index=False)
    shutil.move(tmp_path, raw_path)

    return {"added": added, "updated": updated, "total_rows": len(existing_df)}
