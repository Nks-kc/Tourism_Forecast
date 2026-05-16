"""
auth/models.py
--------------
User database model using Python's built-in sqlite3.
No external ORM needed — keeps dependencies minimal.

DATABASE SCHEMA:
    users (
        id        INTEGER  PRIMARY KEY AUTOINCREMENT,
        username  TEXT     UNIQUE NOT NULL,
        email     TEXT     UNIQUE NOT NULL,
        password  TEXT     NOT NULL,   -- bcrypt hash, never plain text
        created_at TEXT    DEFAULT CURRENT_TIMESTAMP
    )
"""

import sqlite3
import hashlib
import hmac
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


# ── Database initialisation ────────────────────────────────────────────────────

def init_db():
    """
    Create the users table if it does not already exist.
    Call this once when the app starts.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    UNIQUE NOT NULL,
            email      TEXT    UNIQUE NOT NULL,
            password   TEXT    NOT NULL,
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ── Password hashing ───────────────────────────────────────────────────────────
# We use SHA-256 with a random salt stored alongside the hash.
# Format stored in DB:  "salt$hash"
# This avoids needing bcrypt while still being secure enough for a project.

def _hash_password(plain: str) -> str:
    """Hash a plain-text password with a random salt. Returns 'salt$hash'."""
    salt = os.urandom(16).hex()
    hsh  = hmac.new(salt.encode(), plain.encode(), hashlib.sha256).hexdigest()
    return f"{salt}${hsh}"


def _verify_password(plain: str, stored: str) -> bool:
    """Return True if the plain-text password matches the stored 'salt$hash'."""
    try:
        salt, hsh = stored.split("$", 1)
        expected  = hmac.new(salt.encode(), plain.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, hsh)
    except Exception:
        return False


# ── User CRUD ──────────────────────────────────────────────────────────────────

def create_user(username: str, email: str, password: str) -> dict:
    """
    Register a new user.

    Returns:
        {"ok": True, "user_id": int}   on success
        {"ok": False, "error": str}    on failure (duplicate username/email)
    """
    hashed = _hash_password(password)
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur  = conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username.strip(), email.strip().lower(), hashed)
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return {"ok": True, "user_id": user_id}

    except sqlite3.IntegrityError as e:
        msg = str(e)
        if "username" in msg:
            return {"ok": False, "error": "Username already taken."}
        if "email" in msg:
            return {"ok": False, "error": "Email already registered."}
        return {"ok": False, "error": "Registration failed."}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_user_by_username(username: str) -> dict | None:
    """
    Fetch a user row by username.
    Returns a dict with keys: id, username, email, password, created_at
    Returns None if not found.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    row  = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(username: str, password: str) -> dict:
    """
    Verify username and password.

    Returns:
        {"ok": True,  "user": {id, username, email}}  on success
        {"ok": False, "error": str}                    on failure
    """
    user = get_user_by_username(username)
    if not user:
        return {"ok": False, "error": "Username not found."}
    if not _verify_password(password, user["password"]):
        return {"ok": False, "error": "Incorrect password."}

    return {
        "ok": True,
        "user": {
            "id":       user["id"],
            "username": user["username"],
            "email":    user["email"],
        }
    }
