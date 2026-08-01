from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import config
from auth.models import get_user_by_id
from email_utils import send_email

VALID_TYPES = {"forecast_change", "low_arrival", "seasonal_peak"}
VALID_STATUSES = {"unread", "read", "archived"}

DEFAULT_CHANGE_THRESHOLD_PCT = 10.0
DEFAULT_LOW_ARRIVAL_THRESHOLD = None  # disabled until the user sets one
DEFAULT_PEAK_LOOKAHEAD_DAYS = 30


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_notification_tables() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            title      TEXT    NOT NULL,
            message    TEXT    NOT NULL,
            type       TEXT    NOT NULL,
            country    TEXT,
            status     TEXT    NOT NULL DEFAULT 'unread',
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            read_at    TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, status)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_settings (
            user_id               INTEGER PRIMARY KEY,
            change_threshold_pct  REAL,
            low_arrival_threshold REAL,
            peak_lookahead_days   INTEGER,
            email_enabled         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    # Snapshot of the most recent forecast per (country, horizon, model), used
    # to detect "changed materially compared to the previous forecast".
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS forecast_snapshots (
            country       TEXT    NOT NULL,
            horizon       INTEGER NOT NULL,
            model         TEXT    NOT NULL,
            first_value   REAL    NOT NULL,
            forecasted_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (country, horizon, model)
        )
        """
    )
    conn.commit()
    conn.close()


# --- Settings ---------------------------------------------------------


def get_notification_settings(user_id: int) -> dict:
    init_notification_tables()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM notification_settings WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {
            "change_threshold_pct": DEFAULT_CHANGE_THRESHOLD_PCT,
            "low_arrival_threshold": DEFAULT_LOW_ARRIVAL_THRESHOLD,
            "peak_lookahead_days": DEFAULT_PEAK_LOOKAHEAD_DAYS,
            "email_enabled": True,
        }
    return {
        "change_threshold_pct": row["change_threshold_pct"]
        or DEFAULT_CHANGE_THRESHOLD_PCT,
        "low_arrival_threshold": row["low_arrival_threshold"],
        "peak_lookahead_days": row["peak_lookahead_days"]
        or DEFAULT_PEAK_LOOKAHEAD_DAYS,
        "email_enabled": bool(row["email_enabled"]),
    }


def update_notification_settings(user_id: int, **fields) -> dict:
    init_notification_tables()
    current = get_notification_settings(user_id)
    merged = {**current, **{k: v for k, v in fields.items() if v is not None}}
    conn = _connect()
    conn.execute(
        """
        INSERT INTO notification_settings
            (user_id, change_threshold_pct, low_arrival_threshold, peak_lookahead_days, email_enabled)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            change_threshold_pct = excluded.change_threshold_pct,
            low_arrival_threshold = excluded.low_arrival_threshold,
            peak_lookahead_days = excluded.peak_lookahead_days,
            email_enabled = excluded.email_enabled
        """,
        (
            user_id,
            merged["change_threshold_pct"],
            merged["low_arrival_threshold"],
            merged["peak_lookahead_days"],
            int(bool(merged["email_enabled"])),
        ),
    )
    conn.commit()
    conn.close()
    return get_notification_settings(user_id)


# --- Notifications CRUD -------------------------------------------------


def create_notification(
    user_id: int, title: str, message: str, type_: str, country: str | None = None
) -> dict:
    if type_ not in VALID_TYPES:
        raise ValueError(f"type must be one of {sorted(VALID_TYPES)}.")
    init_notification_tables()
    conn = _connect()
    cur = conn.execute(
        """
        INSERT INTO notifications (user_id, title, message, type, country, status)
        VALUES (?, ?, ?, ?, ?, 'unread')
        """,
        (user_id, title, message, type_, country),
    )
    conn.commit()
    notif_id = cur.lastrowid
    conn.close()
    notification = {
        "id": notif_id,
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": type_,
        "country": country,
        "status": "unread",
    }
    deliver_notification(notification)
    return notification


def deliver_notification(notification: dict) -> None:
    """Fan the notification out to enabled delivery channels.

    Email is sent via SMTP (email_utils.send_email) when the user has
    email_enabled in their notification settings -- not a webhook, since
    each alert needs to reach that specific user's own inbox rather than a
    single fixed destination. SMS/push would plug in here the same way:

        if sms_enabled(notification["user_id"]):
            send_sms(user_phone, notification["message"])
        if push_enabled(notification["user_id"]):
            send_push(user_device_token, notification["message"])
    """
    settings = get_notification_settings(notification["user_id"])
    if not settings["email_enabled"]:
        return
    user = get_user_by_id(notification["user_id"])
    if not user or not user.get("email"):
        return
    send_email(
        user["email"],
        notification["title"],
        notification["message"],
    )


def list_notifications(user_id: int, status: str | None = None) -> list[dict]:
    init_notification_tables()
    conn = _connect()
    if status:
        if status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}.")
        rows = conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND status = ? "
            "ORDER BY created_at DESC",
            (user_id, status),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _update_status(user_id: int, notif_id: int, status: str, set_read_at: bool) -> dict:
    init_notification_tables()
    conn = _connect()
    read_at = datetime.now(tz=timezone.utc).isoformat() if set_read_at else None
    cur = conn.execute(
        "UPDATE notifications SET status = ?, read_at = COALESCE(?, read_at) "
        "WHERE id = ? AND user_id = ?",
        (status, read_at, notif_id, user_id),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    if not updated:
        return {"ok": False, "error": "Notification not found."}
    return {"ok": True}


def mark_read(user_id: int, notif_id: int) -> dict:
    return _update_status(user_id, notif_id, "read", set_read_at=True)


def mark_all_read(user_id: int) -> dict:
    init_notification_tables()
    conn = _connect()
    now = datetime.now(tz=timezone.utc).isoformat()
    cur = conn.execute(
        "UPDATE notifications SET status = 'read', read_at = ? "
        "WHERE user_id = ? AND status = 'unread'",
        (now, user_id),
    )
    conn.commit()
    count = cur.rowcount
    conn.close()
    return {"ok": True, "updated": count}


def archive_notification(user_id: int, notif_id: int) -> dict:
    return _update_status(user_id, notif_id, "archived", set_read_at=False)


def delete_notification(user_id: int, notif_id: int) -> dict:
    init_notification_tables()
    conn = _connect()
    cur = conn.execute(
        "DELETE FROM notifications WHERE id = ? AND user_id = ?", (notif_id, user_id)
    )
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    if not deleted:
        return {"ok": False, "error": "Notification not found."}
    return {"ok": True}


# --- Forecast snapshots (used by the alert engine) ----------------------


def get_forecast_snapshot(country: str, horizon: int, model: str) -> float | None:
    init_notification_tables()
    conn = _connect()
    row = conn.execute(
        "SELECT first_value FROM forecast_snapshots WHERE country = ? AND horizon = ? AND model = ?",
        (country, horizon, model),
    ).fetchone()
    conn.close()
    return row["first_value"] if row else None


def save_forecast_snapshot(
    country: str, horizon: int, model: str, first_value: float
) -> None:
    init_notification_tables()
    conn = _connect()
    now = datetime.now(tz=timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO forecast_snapshots (country, horizon, model, first_value, forecasted_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(country, horizon, model) DO UPDATE SET
            first_value = excluded.first_value,
            forecasted_at = excluded.forecasted_at
        """,
        (country, horizon, model, first_value, now),
    )
    conn.commit()
    conn.close()
