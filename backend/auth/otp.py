from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

import config
from email_utils import send_email

from auth.models import _hash_password

REGISTER_PURPOSE = "register"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_otp_tables() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_registrations (
            email      TEXT PRIMARY KEY,
            username   TEXT NOT NULL,
            password   TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS otp_codes (
            email             TEXT NOT NULL,
            purpose           TEXT NOT NULL,
            otp_code          TEXT NOT NULL,
            expires_at        TEXT NOT NULL,
            created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
            request_count     INTEGER NOT NULL DEFAULT 0,
            window_started_at TEXT,
            PRIMARY KEY (email, purpose)
        )
        """
    )

    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(otp_codes)")
    }
    if "request_count" not in existing_columns:
        conn.execute(
            "ALTER TABLE otp_codes ADD COLUMN request_count INTEGER NOT NULL DEFAULT 0"
        )
    if "window_started_at" not in existing_columns:
        conn.execute("ALTER TABLE otp_codes ADD COLUMN window_started_at TEXT")
    conn.commit()
    conn.close()

def create_pending_registration(username: str, email: str, password: str) -> dict:
    from auth.models import (
        get_user_by_username,
    )

    username = username.strip()
    email = email.strip().lower()

    if get_user_by_username(username):
        return {"ok": False, "error": "Username already taken."}

    init_otp_tables()
    conn = _connect()
    try:
        username_taken = conn.execute(
            "SELECT 1 FROM pending_registrations WHERE username = ? AND email != ?",
            (username, email),
        ).fetchone()
        if username_taken:
            return {"ok": False, "error": "Username already taken."}

        email_taken = conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (email,)
        ).fetchone()
        if email_taken:
            return {"ok": False, "error": "Email already registered."}

        existing_pending = conn.execute(
            "SELECT username FROM pending_registrations WHERE email = ?", (email,)
        ).fetchone()
        if existing_pending and existing_pending["username"] != username:
            return {
                "ok": False,
                "error": "Email already has a pending registration under a different username.",
            }

        hashed = _hash_password(password)
        conn.execute(
            """
            INSERT INTO pending_registrations (email, username, password, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(email) DO UPDATE SET
                username = excluded.username,
                password = excluded.password,
                created_at = CURRENT_TIMESTAMP
            """,
            (email, username, hashed),
        )
        conn.commit()
        return {"ok": True, "email": email}
    finally:
        conn.close()


def get_pending_registration(email: str) -> dict | None:
    init_otp_tables()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM pending_registrations WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_pending_registration(email: str) -> None:
    init_otp_tables()
    conn = _connect()
    conn.execute(
        "DELETE FROM pending_registrations WHERE email = ?", (email.strip().lower(),)
    )
    conn.commit()
    conn.close()

def _generate_otp() -> str:
    return f"{secrets.randbelow(10**config.OTP_LENGTH):0{config.OTP_LENGTH}d}"


def send_otp(email: str, purpose: str = REGISTER_PURPOSE) -> dict:
    email = email.strip().lower()
    if purpose == REGISTER_PURPOSE and not get_pending_registration(email):
        return {
            "ok": False,
            "reason": "not_pending",
            "error": "No pending registration found for this email. Register first.",
        }

    init_otp_tables()
    now = datetime.now(tz=timezone.utc)
    conn = _connect()
    try:
        existing = conn.execute(
            "SELECT * FROM otp_codes WHERE email = ? AND purpose = ?", (email, purpose)
        ).fetchone()

        request_count = 0
        window_started_at = now

        if existing:
            expires_at = datetime.fromisoformat(existing["expires_at"])
            if now <= expires_at:
                seconds_left = max(0, int((expires_at - now).total_seconds()))
                return {
                    "ok": False,
                    "reason": "otp_still_valid",
                    "retry_after": seconds_left,
                    "error": f"An OTP was already sent and is still valid for "
                    f"{seconds_left} more second(s). Please wait for it to expire "
                    "before requesting a new one.",
                }

            window_started_at = (
                datetime.fromisoformat(existing["window_started_at"])
                if existing["window_started_at"]
                else now
            )
            window_age = (now - window_started_at).total_seconds()
            if window_age < config.OTP_REQUEST_WINDOW_SECONDS:
                request_count = existing["request_count"]
                if request_count >= config.OTP_MAX_REQUESTS_PER_WINDOW:
                    retry_after = int(config.OTP_REQUEST_WINDOW_SECONDS - window_age)
                    return {
                        "ok": False,
                        "reason": "rate_limited",
                        "retry_after": retry_after,
                        "error": f"Too many OTP requests. Please try again in "
                        f"{retry_after} second(s).",
                    }
            else:
                # Window elapsed -- start a fresh one.
                window_started_at = now
                request_count = 0

        otp = _generate_otp()
        expires_at = now + timedelta(seconds=config.OTP_TTL_SECONDS)

        conn.execute(
            """
            INSERT INTO otp_codes
                (email, purpose, otp_code, expires_at, created_at, request_count, window_started_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            ON CONFLICT(email, purpose) DO UPDATE SET
                otp_code = excluded.otp_code,
                expires_at = excluded.expires_at,
                created_at = CURRENT_TIMESTAMP,
                request_count = excluded.request_count,
                window_started_at = excluded.window_started_at
            """,
            (
                email,
                purpose,
                otp,
                expires_at.isoformat(),
                request_count + 1,
                window_started_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    send_email(
        email,
        "Your Tourism Forecast verification code",
        f"Your verification code is {otp}. It expires in {config.OTP_TTL_SECONDS} seconds.",
    )
    return {"ok": True, "expires_in": config.OTP_TTL_SECONDS}


def verify_otp(email: str, otp: str, purpose: str = REGISTER_PURPOSE) -> dict:
    email = email.strip().lower()
    otp = str(otp).strip()
    init_otp_tables()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM otp_codes WHERE email = ? AND purpose = ?", (email, purpose)
    ).fetchone()
    if not row:
        conn.close()
        return {
            "ok": False,
            "error": "No OTP was requested for this email. Click 'Send OTP' first.",
        }

    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now(tz=timezone.utc) > expires_at:
        conn.close()
        return {"ok": False, "error": "OTP has expired. Please request a new one."}

    if not secrets.compare_digest(row["otp_code"], otp):
        conn.close()
        return {"ok": False, "error": "Incorrect OTP."}

    conn.execute(
        "DELETE FROM otp_codes WHERE email = ? AND purpose = ?", (email, purpose)
    )
    conn.commit()
    conn.close()
    return {"ok": True}
