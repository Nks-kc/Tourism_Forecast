from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import config

ALLOWED_HORIZONS = [1, 3, 6, 12]
ALLOWED_THEMES = ["light", "dark", "system"]

DEFAULT_PREFERENCES = {
    "default_horizon": 3,
    "preferred_countries": [],
    "theme": "system",
    "chart_filters": {},
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_preferences_table() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id             INTEGER PRIMARY KEY,
            default_horizon     INTEGER NOT NULL DEFAULT 3,
            preferred_countries TEXT    NOT NULL DEFAULT '[]',
            theme               TEXT    NOT NULL DEFAULT 'system',
            chart_filters       TEXT    NOT NULL DEFAULT '{}',
            updated_at          TEXT    DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "default_horizon": row["default_horizon"],
        "preferred_countries": json.loads(row["preferred_countries"]),
        "theme": row["theme"],
        "chart_filters": json.loads(row["chart_filters"]),
        "updated_at": row["updated_at"],
    }


def get_preferences(user_id: int) -> dict:
    init_preferences_table()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {**DEFAULT_PREFERENCES, "updated_at": None}
    return _row_to_dict(row)


def validate_preferences(fields: dict) -> str | None:
    """Return an error message if invalid, else None."""
    if "default_horizon" in fields:
        try:
            horizon = int(fields["default_horizon"])
        except (TypeError, ValueError):
            return "'default_horizon' must be an integer."
        if horizon not in ALLOWED_HORIZONS:
            return f"'default_horizon' must be one of {ALLOWED_HORIZONS}."
    if "theme" in fields and fields["theme"] not in ALLOWED_THEMES:
        return f"'theme' must be one of {ALLOWED_THEMES}."
    if "preferred_countries" in fields and not isinstance(
        fields["preferred_countries"], list
    ):
        return "'preferred_countries' must be a list of strings."
    if "chart_filters" in fields and not isinstance(fields["chart_filters"], dict):
        return "'chart_filters' must be an object."
    return None


def update_preferences(user_id: int, **fields) -> dict:
    error = validate_preferences(fields)
    if error:
        return {"ok": False, "error": error}

    init_preferences_table()
    current = get_preferences(user_id)
    merged = {**current, **{k: v for k, v in fields.items() if v is not None}}
    now = datetime.now(tz=timezone.utc).isoformat()

    conn = _connect()
    conn.execute(
        """
        INSERT INTO user_preferences
            (user_id, default_horizon, preferred_countries, theme, chart_filters, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            default_horizon = excluded.default_horizon,
            preferred_countries = excluded.preferred_countries,
            theme = excluded.theme,
            chart_filters = excluded.chart_filters,
            updated_at = excluded.updated_at
        """,
        (
            user_id,
            int(merged["default_horizon"]),
            json.dumps(merged["preferred_countries"]),
            merged["theme"],
            json.dumps(merged["chart_filters"]),
            now,
        ),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "preferences": get_preferences(user_id)}


def reset_preferences(user_id: int) -> dict:
    init_preferences_table()
    conn = _connect()
    conn.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "preferences": get_preferences(user_id)}
