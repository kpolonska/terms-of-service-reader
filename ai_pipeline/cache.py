"""Cache with two interchangeable backends: SQLite (local dev) or Postgres (Vercel).

Backend is chosen at runtime via env vars:
- If DATABASE_URL is set and starts with postgres:// or postgresql://, use Postgres.
- Otherwise fall back to SQLite at DATABASE_PATH (default: analyses.db).

Public functions (get_cached, store_result, subscribe, ...) keep identical signatures,
so callers do not care which backend is active.
"""

import hashlib
import json
import sqlite3
import os
from datetime import datetime, timezone

try:
    import psycopg
    from psycopg.rows import dict_row
    _PSYCOPG_AVAILABLE = True
except ImportError:
    _PSYCOPG_AVAILABLE = False


def _use_postgres() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return url.startswith(("postgres://", "postgresql://")) and _PSYCOPG_AVAILABLE


def _sqlite_path() -> str:
    return os.environ.get("DATABASE_PATH", "analyses.db")


def init_db():
    if _use_postgres():
        _init_pg()
    else:
        _init_sqlite()


# ---------- SQLite backend ----------

def _sqlite_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_sqlite_path())
    conn.row_factory = sqlite3.Row
    return conn


def _sqlite_migrate_analyses(conn: sqlite3.Connection):
    """Add profile column if it doesn't exist (legacy schema fix)."""
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


def _init_sqlite():
    with _sqlite_connection() as conn:
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
        _sqlite_migrate_analyses(conn)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_text_hash_profile ON analyses (text_hash, profile)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_domain ON analyses (domain, analyzed_at)")
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


def _sqlite_get_two_latest_for_domain(domain: str) -> list[dict]:
    with _sqlite_connection() as conn:
        rows = conn.execute(
            "SELECT result_json, analyzed_at FROM analyses WHERE domain = ? ORDER BY analyzed_at DESC LIMIT 2",
            (domain,),
        ).fetchall()
    return [{"result": json.loads(r["result_json"]), "analyzed_at": r["analyzed_at"]} for r in rows]


def _sqlite_get_cached_alternatives(domain: str) -> list | None:
    with _sqlite_connection() as conn:
        row = conn.execute(
            "SELECT alternatives_json FROM alternatives_cache WHERE domain = ?", (domain,)
        ).fetchone()
    return json.loads(row["alternatives_json"]) if row else None


def _sqlite_store_alternatives(domain: str, alternatives: list):
    with _sqlite_connection() as conn:
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


def _sqlite_subscribe(domain: str):
    with _sqlite_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscriptions (domain, subscribed_at) VALUES (?, ?)",
            (domain, datetime.now(timezone.utc).isoformat()),
        )


def _sqlite_unsubscribe(domain: str):
    with _sqlite_connection() as conn:
        conn.execute("DELETE FROM subscriptions WHERE domain = ?", (domain,))


def _sqlite_get_subscriptions() -> list[str]:
    with _sqlite_connection() as conn:
        rows = conn.execute("SELECT domain FROM subscriptions ORDER BY subscribed_at DESC").fetchall()
    return [r["domain"] for r in rows]


def _sqlite_is_subscribed(domain: str) -> bool:
    with _sqlite_connection() as conn:
        row = conn.execute("SELECT 1 FROM subscriptions WHERE domain = ?", (domain,)).fetchone()
    return row is not None


def _sqlite_get_cached(text_hash: str, profile: str) -> dict | None:
    with _sqlite_connection() as conn:
        row = conn.execute(
            "SELECT result_json FROM analyses WHERE text_hash = ? AND profile = ? ORDER BY analyzed_at DESC LIMIT 1",
            (text_hash, profile),
        ).fetchone()
    return json.loads(row["result_json"]) if row else None


def _sqlite_store_result(text_hash: str, domain: str | None, result: dict, profile: str):
    with _sqlite_connection() as conn:
        conn.execute(
            "INSERT INTO analyses (text_hash, domain, profile, result_json, analyzed_at) VALUES (?, ?, ?, ?, ?)",
            (text_hash, domain, profile, json.dumps(result), datetime.now(timezone.utc).isoformat()),
        )


# ---------- Postgres backend ----------

def _pg_connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def _init_pg():
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id SERIAL PRIMARY KEY,
                text_hash TEXT NOT NULL,
                domain TEXT,
                profile TEXT DEFAULT 'general',
                result_json TEXT NOT NULL,
                analyzed_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_analyses_text_hash_profile ON analyses (text_hash, profile)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_analyses_domain ON analyses (domain, analyzed_at)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alternatives_cache (
                domain TEXT PRIMARY KEY,
                alternatives_json TEXT NOT NULL,
                generated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                domain TEXT PRIMARY KEY,
                subscribed_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


def _pg_get_two_latest_for_domain(domain: str) -> list[dict]:
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT result_json, analyzed_at FROM analyses WHERE domain = %s ORDER BY analyzed_at DESC LIMIT 2",
            (domain,),
        )
        rows = cur.fetchall()
    return [{"result": json.loads(r["result_json"]), "analyzed_at": r["analyzed_at"].isoformat() if r["analyzed_at"] else None} for r in rows]


def _pg_get_cached_alternatives(domain: str) -> list | None:
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT alternatives_json FROM alternatives_cache WHERE domain = %s", (domain,))
        row = cur.fetchone()
    return json.loads(row["alternatives_json"]) if row else None


def _pg_store_alternatives(domain: str, alternatives: list):
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO alternatives_cache (domain, alternatives_json, generated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (domain) DO UPDATE SET
                alternatives_json = EXCLUDED.alternatives_json,
                generated_at = EXCLUDED.generated_at
            """,
            (domain, json.dumps(alternatives)),
        )


def _pg_subscribe(domain: str):
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO subscriptions (domain, subscribed_at) VALUES (%s, NOW()) ON CONFLICT (domain) DO NOTHING",
            (domain,),
        )


def _pg_unsubscribe(domain: str):
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM subscriptions WHERE domain = %s", (domain,))


def _pg_get_subscriptions() -> list[str]:
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT domain FROM subscriptions ORDER BY subscribed_at DESC")
        rows = cur.fetchall()
    return [r["domain"] for r in rows]


def _pg_is_subscribed(domain: str) -> bool:
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM subscriptions WHERE domain = %s", (domain,))
        row = cur.fetchone()
    return row is not None


def _pg_get_cached(text_hash: str, profile: str) -> dict | None:
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT result_json FROM analyses WHERE text_hash = %s AND profile = %s ORDER BY analyzed_at DESC LIMIT 1",
            (text_hash, profile),
        )
        row = cur.fetchone()
    return json.loads(row["result_json"]) if row else None


def _pg_store_result(text_hash: str, domain: str | None, result: dict, profile: str):
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO analyses (text_hash, domain, profile, result_json, analyzed_at) VALUES (%s, %s, %s, %s, NOW())",
            (text_hash, domain, profile, json.dumps(result)),
        )


# ---------- Public API (dispatch) ----------

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_cached(text_hash: str, profile: str = "general") -> dict | None:
    init_db()
    return _pg_get_cached(text_hash, profile) if _use_postgres() else _sqlite_get_cached(text_hash, profile)


def store_result(text_hash: str, domain: str | None, result: dict, profile: str = "general"):
    init_db()
    return _pg_store_result(text_hash, domain, result, profile) if _use_postgres() else _sqlite_store_result(text_hash, domain, result, profile)


def get_two_latest_for_domain(domain: str) -> list[dict]:
    init_db()
    return _pg_get_two_latest_for_domain(domain) if _use_postgres() else _sqlite_get_two_latest_for_domain(domain)


def get_cached_alternatives(domain: str) -> list | None:
    init_db()
    return _pg_get_cached_alternatives(domain) if _use_postgres() else _sqlite_get_cached_alternatives(domain)


def store_alternatives(domain: str, alternatives: list):
    init_db()
    return _pg_store_alternatives(domain, alternatives) if _use_postgres() else _sqlite_store_alternatives(domain, alternatives)


def subscribe(domain: str):
    init_db()
    return _pg_subscribe(domain) if _use_postgres() else _sqlite_subscribe(domain)


def unsubscribe(domain: str):
    init_db()
    return _pg_unsubscribe(domain) if _use_postgres() else _sqlite_unsubscribe(domain)


def get_subscriptions() -> list[str]:
    init_db()
    return _pg_get_subscriptions() if _use_postgres() else _sqlite_get_subscriptions()


def is_subscribed(domain: str) -> bool:
    init_db()
    return _pg_is_subscribed(domain) if _use_postgres() else _sqlite_is_subscribed(domain)
