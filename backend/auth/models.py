import hashlib
import hmac
import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    UNIQUE NOT NULL,
            email      TEXT    UNIQUE NOT NULL,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL DEFAULT 'user',
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Migration for DBs created before 'role' existed
    existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
    if "role" not in existing_columns:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
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


def create_user(username: str, email: str, password: str, role: str = "user") -> dict:
    hashed = _hash_password(password)
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cur = conn.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            (username.strip(), email.strip().lower(), hashed, role),
        )
        conn.commit()
        user_id = cur.lastrowid
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
    finally:
        conn.close()


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
            "role": user["role"],
        },
    }

def list_users() -> list[dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, username, email, role, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def set_user_role(username: str, role: str) -> None:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        "UPDATE users SET role = ? WHERE username = ?", (role, username.strip())
    )
    conn.commit()
    conn.close()