from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_reports_table() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id      INTEGER NOT NULL,
            owner         TEXT    NOT NULL,
            report_type   TEXT    NOT NULL,
            countries     TEXT    NOT NULL,
            file_path     TEXT    NOT NULL,
            generated_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def save_report_metadata(
    owner_id: int, owner: str, report_type: str, countries: list[str], file_path: str
) -> dict:
    init_reports_table()
    conn = _connect()
    now = datetime.now(tz=timezone.utc).isoformat()
    cur = conn.execute(
        """
        INSERT INTO reports (owner_id, owner, report_type, countries, file_path, generated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (owner_id, owner, report_type, json.dumps(countries), file_path, now),
    )
    conn.commit()
    report_id = cur.lastrowid
    conn.close()
    return {
        "id": report_id,
        "owner_id": owner_id,
        "owner": owner,
        "report_type": report_type,
        "countries": countries,
        "file_path": file_path,
        "generated_at": now,
    }


def list_reports(owner_id: int) -> list[dict]:
    init_reports_table()
    conn = _connect()
    rows = conn.execute(
        "SELECT id, owner, report_type, countries, generated_at FROM reports "
        "WHERE owner_id = ? ORDER BY generated_at DESC",
        (owner_id,),
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        d["countries"] = json.loads(d["countries"])
        results.append(d)
    return results


def get_report(owner_id: int, report_id: int) -> dict | None:
    init_reports_table()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM reports WHERE id = ? AND owner_id = ?", (report_id, owner_id)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["countries"] = json.loads(d["countries"])
    return d
