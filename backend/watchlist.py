from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_watchlist_tables() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            country    TEXT    NOT NULL,
            position   INTEGER NOT NULL,
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, country)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id)")
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
    conn.commit()
    conn.close()


# --- Watchlist ---------------------------------------------------------


def get_watchlist(user_id: int) -> list[dict]:
    init_watchlist_tables()
    conn = _connect()
    rows = conn.execute(
        "SELECT country, position, created_at FROM watchlist "
        "WHERE user_id = ? ORDER BY position ASC, id ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_country(user_id: int, country: str) -> dict:
    country = country.strip()
    if not country:
        return {"ok": False, "error": "country must be a non-empty string."}
    init_watchlist_tables()
    conn = _connect()
    try:
        next_position = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM watchlist WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO watchlist (user_id, country, position) VALUES (?, ?, ?)",
            (user_id, country, next_position),
        )
        conn.commit()
        return {"ok": True}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": f"'{country}' is already on the watchlist."}
    finally:
        conn.close()


def remove_country(user_id: int, country: str) -> dict:
    init_watchlist_tables()
    conn = _connect()
    cur = conn.execute(
        "DELETE FROM watchlist WHERE user_id = ? AND country = ?",
        (user_id, country.strip()),
    )
    conn.commit()
    removed = cur.rowcount > 0
    conn.close()
    if not removed:
        return {"ok": False, "error": f"'{country}' is not on the watchlist."}
    return {"ok": True}


def reorder_watchlist(user_id: int, ordered_countries: list[str]) -> dict:
    """Reprioritize the watchlist. `ordered_countries` must contain exactly
    the countries currently on the user's watchlist, in the desired order."""
    init_watchlist_tables()
    current = {row["country"] for row in get_watchlist(user_id)}
    incoming = [c.strip() for c in ordered_countries]
    if set(incoming) != current or len(incoming) != len(current):
        return {
            "ok": False,
            "error": "ordered countries must exactly match the current watchlist.",
        }
    conn = _connect()
    for position, country in enumerate(incoming):
        conn.execute(
            "UPDATE watchlist SET position = ? WHERE user_id = ? AND country = ?",
            (position, user_id, country),
        )
    conn.commit()
    conn.close()
    return {"ok": True}


# --- Last viewed ---------------------------------------------------------


def set_last_viewed(
    user_id: int, country: str | None = None, dashboard: str | None = None
) -> None:
    init_watchlist_tables()
    conn = _connect()
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
            country = excluded.country,
            dashboard = excluded.dashboard,
            updated_at = excluded.updated_at
        """,
        (user_id, new_country, new_dashboard, now),
    )
    conn.commit()
    conn.close()


def get_last_viewed(user_id: int) -> dict | None:
    init_watchlist_tables()
    conn = _connect()
    row = conn.execute(
        "SELECT country, dashboard, updated_at FROM last_viewed WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
