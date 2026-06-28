import hashlib
import json
import sqlite3
import os
from datetime import datetime, timezone


def _db_path() -> str:
    return os.environ.get("DATABASE_PATH", "analyses.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_analyses_table(conn: sqlite3.Connection):
    """Add profile column if it doesn't exist."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='analyses'"
    ).fetchone()
    if row:
        sql = row["sql"] or ""
        if "profile" not in sql:
            conn.execute("ALTER TABLE analyses ADD COLUMN profile TEXT DEFAULT 'general'")
        if "UNIQUE" in sql.upper():
            conn.execute("ALTER TABLE analyses RENAME TO _analyses_old")
            conn.execute("""
                CREATE TABLE analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_hash TEXT NOT NULL,
                    domain TEXT,
                    profile TEXT DEFAULT 'general',
                    result_json TEXT NOT NULL,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(
                "INSERT INTO analyses (id, text_hash, domain, profile, result_json, analyzed_at) "
                "SELECT id, text_hash, domain, COALESCE(profile, 'general'), result_json, analyzed_at FROM _analyses_old"
            )
            conn.execute("DROP TABLE _analyses_old")


def init_db():
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT NOT NULL,
                domain TEXT,
                profile TEXT DEFAULT 'general',
                result_json TEXT NOT NULL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        _migrate_analyses_table(conn)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_analyses_text_hash_profile ON analyses (text_hash, profile)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_analyses_domain ON analyses (domain, analyzed_at)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alternatives_cache (
                domain TEXT PRIMARY KEY,
                alternatives_json TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                domain TEXT PRIMARY KEY,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_two_latest_for_domain(domain: str) -> list[dict]:
    """Return up to 2 most recent distinct analyses for a domain, newest first."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT result_json, analyzed_at FROM analyses WHERE domain = ? ORDER BY analyzed_at DESC LIMIT 2",
            (domain,),
        ).fetchall()
    return [{"result": json.loads(r["result_json"]), "analyzed_at": r["analyzed_at"]} for r in rows]


def get_cached_alternatives(domain: str) -> list | None:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT alternatives_json FROM alternatives_cache WHERE domain = ?", (domain,)
        ).fetchone()
    return json.loads(row["alternatives_json"]) if row else None


def store_alternatives(domain: str, alternatives: list):
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO alternatives_cache (domain, alternatives_json, generated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                alternatives_json = excluded.alternatives_json,
                generated_at = excluded.generated_at
            """,
            (domain, json.dumps(alternatives), datetime.now(timezone.utc).isoformat()),
        )


def subscribe(domain: str):
    with _get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscriptions (domain, subscribed_at) VALUES (?, ?)",
            (domain, datetime.now(timezone.utc).isoformat()),
        )


def unsubscribe(domain: str):
    with _get_connection() as conn:
        conn.execute("DELETE FROM subscriptions WHERE domain = ?", (domain,))


def get_subscriptions() -> list[str]:
    with _get_connection() as conn:
        rows = conn.execute("SELECT domain FROM subscriptions ORDER BY subscribed_at DESC").fetchall()
    return [r["domain"] for r in rows]


def is_subscribed(domain: str) -> bool:
    with _get_connection() as conn:
        row = conn.execute("SELECT 1 FROM subscriptions WHERE domain = ?", (domain,)).fetchone()
    return row is not None


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_cached(text_hash: str, profile: str = "general") -> dict | None:
    init_db()
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT result_json FROM analyses WHERE text_hash = ? AND profile = ? ORDER BY analyzed_at DESC LIMIT 1",
            (text_hash, profile),
        ).fetchone()
    if row:
        return json.loads(row["result_json"])
    return None


def store_result(text_hash: str, domain: str | None, result: dict, profile: str = "general"):
    init_db()
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO analyses (text_hash, domain, profile, result_json, analyzed_at) VALUES (?, ?, ?, ?, ?)",
            (text_hash, domain, profile, json.dumps(result), datetime.now(timezone.utc).isoformat()),
        )
