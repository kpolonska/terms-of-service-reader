import hashlib
import json
import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get("DATABASE_PATH", "analyses.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT UNIQUE NOT NULL,
                domain TEXT,
                result_json TEXT NOT NULL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_cached(text_hash: str) -> dict | None:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT result_json FROM analyses WHERE text_hash = ?", (text_hash,)
        ).fetchone()
    if row:
        return json.loads(row["result_json"])
    return None


def store_result(text_hash: str, domain: str | None, result: dict):
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analyses (text_hash, domain, result_json, analyzed_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(text_hash) DO NOTHING
            """,
            (text_hash, domain, json.dumps(result), datetime.now(timezone.utc).isoformat()),
        )


init_db()
