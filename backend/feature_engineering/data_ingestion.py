from __future__ import annotations

import data_store
import pandas as pd
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
        except (ValueError, TypeError):
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
        except (ValueError, TypeError):
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
    Add or update one or more country/month arrival records in the database.

    Each entry needs 'country' and 'arrivals', plus either its own 'date'
    (YYYY-MM-DD) or it will fall back to the shared top-level year/month.
    Existing (country, month) rows are updated in place when overwrite=True;
    otherwise a duplicate raises DataIngestionError.
    """
    if not entries:
        raise DataIngestionError("No entries provided.")

    new_rows = [_normalize_entry(e, year, month) for e in entries]

    data_store.init_tourism_tables()
    conn = data_store._connect()
    try:
        added, updated = [], []
        for row in new_rows:
            date_str = row[DATE_COLUMN].strftime("%Y-%m-%d")
            label = f"{row[COUNTRY_COLUMN]} ({row[DATE_COLUMN].strftime('%Y-%m')})"
            exists = conn.execute(
                "SELECT 1 FROM country_arrivals WHERE date = ? AND country = ?",
                (date_str, row[COUNTRY_COLUMN]),
            ).fetchone()
            if exists:
                if not overwrite:
                    raise DataIngestionError(f"Data for {label} already exists.")
                updated.append(label)
            else:
                added.append(label)
    finally:
        conn.close()

    data_store.upsert_country_arrivals(
        [
            {
                "date": row[DATE_COLUMN],
                "country": row[COUNTRY_COLUMN],
                "arrivals": row[TARGET_COLUMN],
                "year": row[YEAR_COLUMN],
                "month": row[MONTH_COLUMN],
            }
            for row in new_rows
        ]
    )

    conn = data_store._connect()
    try:
        total_rows = conn.execute("SELECT COUNT(*) FROM country_arrivals").fetchone()[0]
    finally:
        conn.close()

    return {"added": added, "updated": updated, "total_rows": total_rows}
