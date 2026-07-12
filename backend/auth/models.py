import sqlite3
import hashlib
import hmac
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        "\n        CREATE TABLE IF NOT EXISTS users (\n" \
        "id         INTEGER PRIMARY KEY AUTOINCREMENT,\n" \
        "username   TEXT    UNIQUE NOT NULL,\n" \
        "email      TEXT    UNIQUE NOT NULL,\n" \
        "password   TEXT    NOT NULL,\n" \
        "created_at TEXT    DEFAULT CURRENT_TIMESTAMP\n)\n"
    )
    conn.commit()
    conn.close()


def _hash_password(plain: str) -> str:
    salt = os.urandom(16).hex()
    hsh = hmac.new(salt.encode(), plain.encode(), hashlib.sha256).hexdigest()
    return f"{salt}${hsh}"


def _verify_password(plain: str, stored: str) -> bool:
    try:
        salt, hsh = stored.split("$", 1)
        expected = hmac.new(salt.encode(), plain.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, hsh)
    except Exception:
        return False


def create_user(username: str, email: str, password: str) -> dict:
    hashed = _hash_password(password)
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username.strip(), email.strip().lower(), hashed),
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
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(username: str, password: str) -> dict:
    user = get_user_by_username(username)
    if not user:
        return {"ok": False, "error": "Username not found."}
    if not _verify_password(password, user["password"]):
        return {"ok": False, "error": "Incorrect password."}
    return {
        "ok": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
        },
    }
