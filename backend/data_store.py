"""SQLite-backed storage for the two arrivals datasets the project uses:

- country_arrivals: monthly arrivals per source country (drives per-country
  forecasting, cross-validated against the NTB workbook in data/external/).
- national_arrivals: the official monthly nationwide total (drives the
  nationwide/"total" forecasting models directly -- it is NOT derived by
  summing country_arrivals).

Both tables live in the same SQLite file as the users table (config.DATABASE_PATH).
This module intentionally does `import config` and reads `config.DATABASE_PATH`
at call time (never `from config import DATABASE_PATH`), so tests that
monkeypatch config.DATABASE_PATH -- and any future code that changes it at
runtime -- are respected. See auth/models.py's docstring history for why this
matters: importing the value by name binds it once, at import time, and stops
tracking changes to the config module afterwards.
"""

from __future__ import annotations

import sqlite3

import config
import pandas as pd


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_tourism_tables() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS country_arrivals (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT    NOT NULL,
            country  TEXT    NOT NULL,
            arrivals REAL    NOT NULL,
            year     INTEGER NOT NULL,
            month    INTEGER NOT NULL,
            UNIQUE(date, country)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_country_arrivals_country "
        "ON country_arrivals(country)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS national_arrivals (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT    NOT NULL UNIQUE,
            arrivals REAL    NOT NULL,
            year     INTEGER NOT NULL,
            month    INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# --- Country-level arrivals --------------------------------------------------


def load_country_arrivals() -> pd.DataFrame:
    """Return every (date, country, arrivals) row, as a DataFrame with the
    same columns the old tourism_country_long.csv had: date, country,
    arrivals, year, month."""
    init_tourism_tables()
    conn = _connect()
    df = pd.read_sql_query(
        "SELECT date, country, arrivals, year, month FROM country_arrivals "
        "ORDER BY country, date",
        conn,
    )
    conn.close()
    if df.empty:
        raise FileNotFoundError(
            "country_arrivals table is empty. Run 'python migrate_data_to_db.py' "
            "to load data/raw/tourism_country_long.csv into the database."
        )
    return df


def upsert_country_arrivals(rows: list[dict]) -> dict:
    """Insert new (date, country) rows or overwrite the arrivals value for
    ones that already exist. Each row needs: date (YYYY-MM-DD string or
    Timestamp), country, arrivals, year, month."""
    if not rows:
        return {"added": 0, "updated": 0}
    init_tourism_tables()
    conn = _connect()
    added = updated = 0
    for row in rows:
        date_str = pd.Timestamp(row["date"]).strftime("%Y-%m-%d")
        existing = conn.execute(
            "SELECT 1 FROM country_arrivals WHERE date = ? AND country = ?",
            (date_str, row["country"]),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO country_arrivals (date, country, arrivals, year, month)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date, country) DO UPDATE SET arrivals = excluded.arrivals
            """,
            (
                date_str,
                row["country"],
                float(row["arrivals"]),
                int(row["year"]),
                int(row["month"]),
            ),
        )
        if existing:
            updated += 1
        else:
            added += 1
    conn.commit()
    conn.close()
    return {"added": added, "updated": updated}


# --- Nationwide arrivals ------------------------------------------------------


def load_national_arrivals() -> pd.DataFrame:
    """Return every (date, arrivals) row for the official nationwide total,
    as a DataFrame with columns: date, arrivals, year, month."""
    init_tourism_tables()
    conn = _connect()
    df = pd.read_sql_query(
        "SELECT date, arrivals, year, month FROM national_arrivals ORDER BY date",
        conn,
    )
    conn.close()
    if df.empty:
        raise FileNotFoundError(
            "national_arrivals table is empty. Run 'python migrate_data_to_db.py' "
            "to load data/raw/tourism_monthly_corrected.csv into the database."
        )
    return df


def upsert_national_arrivals(rows: list[dict]) -> dict:
    """Insert new dates or overwrite the arrivals value for ones that already
    exist. Each row needs: date, arrivals, year, month."""
    if not rows:
        return {"added": 0, "updated": 0}
    init_tourism_tables()
    conn = _connect()
    added = updated = 0
    for row in rows:
        date_str = pd.Timestamp(row["date"]).strftime("%Y-%m-%d")
        existing = conn.execute(
            "SELECT 1 FROM national_arrivals WHERE date = ?", (date_str,)
        ).fetchone()
        conn.execute(
            """
            INSERT INTO national_arrivals (date, arrivals, year, month)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET arrivals = excluded.arrivals
            """,
            (date_str, float(row["arrivals"]), int(row["year"]), int(row["month"])),
        )
        if existing:
            updated += 1
        else:
            added += 1
    conn.commit()
    conn.close()
    return {"added": added, "updated": updated}
