import sqlite3
import hashlib
import hmac
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def init_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT    UNIQUE NOT NULL,
            email        TEXT    UNIQUE NOT NULL,
            password     TEXT    NOT NULL,
            role         TEXT    NOT NULL DEFAULT 'user',
            is_permanent INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Migrations for DBs created before these columns existed
    existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
    if "role" not in existing_columns:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    if "is_permanent" not in existing_columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN is_permanent INTEGER NOT NULL DEFAULT 0"
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


def create_user(username: str, email: str, password: str, role: str = "user") -> dict:
    hashed = _hash_password(password)
    conn = sqlite3.connect(config.DATABASE_PATH)
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
    conn = sqlite3.connect(config.DATABASE_PATH)
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
            "is_permanent": bool(user.get("is_permanent", 0)),
        },
    }


def list_users() -> list[dict]:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, username, email, role, is_permanent, created_at "
        "FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def set_user_role(username: str, role: str) -> dict:
    """Change a user's role.

    Refuses to change the role of the permanent admin account (is_permanent = 1)
    away from 'admin' — this applies no matter who is making the request,
    including the permanent admin trying to demote themselves.
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT is_permanent FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    if row is None:
        conn.close()
        return {"ok": False, "error": f"User '{username}' not found."}
    if row["is_permanent"] and role != "admin":
        conn.close()
        return {
            "ok": False,
            "error": "This account is the permanent administrator and cannot be demoted.",
        }
    conn.execute(
        "UPDATE users SET role = ? WHERE username = ?", (role, username.strip())
    )
    conn.commit()
    conn.close()
    return {"ok": True}


def set_permanent_admin(username: str) -> dict:
    """Mark an existing user as the permanent admin: promotes them to 'admin'
    (if needed) and sets is_permanent = 1, so no admin — including this user —
    can ever demote this account through the normal role-change endpoint.

    Intended to be run once, deliberately, e.g. from create_admin.py, rather
    than being reachable through any API route.
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, role FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    if row is None:
        conn.close()
        return {"ok": False, "error": f"User '{username}' not found."}

    other_permanent = conn.execute(
        "SELECT username FROM users WHERE is_permanent = 1 AND username != ?",
        (username.strip(),),
    ).fetchone()

    conn.execute(
        "UPDATE users SET role = 'admin', is_permanent = 1 WHERE id = ?",
        (row["id"],),
    )
    conn.commit()
    conn.close()

    result = {"ok": True}
    if other_permanent:
        result["warning"] = (
            f"'{other_permanent['username']}' was already a permanent admin. "
            f"There are now two permanent admin accounts."
        )
    return result
