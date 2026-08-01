"""SQLite-backed storage for the watchlist feature.

All SQL operations against the `watchlist` table live here.  The module
intentionally does `import config` and reads `config.DATABASE_PATH` at call
time (never `from config import DATABASE_PATH`), so tests that monkeypatch
config.DATABASE_PATH — and any future code that changes it at runtime — are
respected.  Importing the value by name would bind it once at import time and
stop tracking changes to the config module afterwards.  This is the same
pattern used by data_store.py.
"""

from __future__ import annotations

import sqlite3

import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_watchlist_table() -> None:
    """Create the watchlist table (and its index) if they do not exist.
    Safe to call repeatedly — uses IF NOT EXISTS throughout."""
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            country   TEXT    NOT NULL CHECK(length(country) >= 1 AND length(country) <= 100),
            pinned_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, country)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id)"
    )
    conn.commit()
    conn.close()


def get_watchlist(user_id: int) -> list[str]:
    """Return country names pinned by user_id, ordered by pinned_at ASC
    (oldest pin first)."""
    conn = _connect()
    rows = conn.execute(
        "SELECT country FROM watchlist WHERE user_id = ? ORDER BY pinned_at ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def pin_country(user_id: int, country: str) -> dict:
    """Insert (user_id, country) using INSERT OR IGNORE so duplicate pins
    are silently dropped rather than raising an error.
    Always returns {"ok": True, "country": country}."""
    conn = _connect()
    conn.execute(
        "INSERT OR IGNORE INTO watchlist (user_id, country) VALUES (?, ?)",
        (user_id, country),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "country": country}


def unpin_country(user_id: int, country: str) -> dict:
    """Delete the (user_id, country) row.  Returns {"ok": True, "country":
    country} even when the row was absent — the caller does not need to know
    whether a deletion actually occurred."""
    conn = _connect()
    conn.execute(
        "DELETE FROM watchlist WHERE user_id = ? AND country = ?",
        (user_id, country),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "country": country}


def get_watchlist_count(user_id: int) -> int:
    """Return the number of countries currently pinned by user_id."""
    conn = _connect()
    row = conn.execute(
        "SELECT COUNT(*) FROM watchlist WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return row[0]


# ── Last-viewed helpers ───────────────────────────────────────────────────────


def _init_last_viewed_table(conn: sqlite3.Connection) -> None:
    """Create the last_viewed table if it does not exist (called inside an
    already-open connection so the caller can commit in one shot)."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS last_viewed (
            user_id    INTEGER PRIMARY KEY,
            country    TEXT,
            dashboard  TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def init_watchlist_tables() -> None:
    """Create both the watchlist table and the last_viewed table.
    Safe to call repeatedly — uses IF NOT EXISTS throughout."""
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            country   TEXT    NOT NULL CHECK(length(country) >= 1 AND length(country) <= 100),
            pinned_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, country)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id)"
    )
    _init_last_viewed_table(conn)
    conn.commit()
    conn.close()


def get_last_viewed(user_id: int) -> dict | None:
    """Return the last-viewed state for user_id, or None if never set."""
    conn = _connect()
    row = conn.execute(
        "SELECT country, dashboard, updated_at FROM last_viewed WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def set_last_viewed(
    user_id: int, country: str | None = None, dashboard: str | None = None
) -> None:
    """Upsert the last-viewed country/dashboard for user_id.
    Pass only the field(s) you want to update; the other will be preserved."""
    from datetime import datetime, timezone

    conn = _connect()
    _init_last_viewed_table(conn)
    now = datetime.now(tz=timezone.utc).isoformat()
    existing = conn.execute(
        "SELECT country, dashboard FROM last_viewed WHERE user_id = ?", (user_id,)
    ).fetchone()
    new_country = (
        country if country is not None else (existing["country"] if existing else None)
    )
    new_dashboard = (
        dashboard
        if dashboard is not None
        else (existing["dashboard"] if existing else None)
    )
    conn.execute(
        """
        INSERT INTO last_viewed (user_id, country, dashboard, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            country    = excluded.country,
            dashboard  = excluded.dashboard,
            updated_at = excluded.updated_at
        """,
        (user_id, new_country, new_dashboard, now),
    )
    conn.commit()
    conn.close()
