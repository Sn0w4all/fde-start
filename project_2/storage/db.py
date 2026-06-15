"""SQLite-backed authorization store.

Only the fact of authorization is persisted (no conversation context).
Table ``users``: tg_id PK, authorized_at (UTC ISO-8601 string).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import aiosqlite

_DB_PATH = "data/auth.db"


def configure(db_path: str) -> None:
    """Set the database file location (call once at startup)."""
    global _DB_PATH
    _DB_PATH = db_path


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


async def init_db() -> None:
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                tg_id        INTEGER PRIMARY KEY,
                authorized_at TEXT NOT NULL
            )
            """
        )
        await db.commit()


async def is_authorized(tg_id: int) -> bool:
    async with aiosqlite.connect(_DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM users WHERE tg_id = ?", (tg_id,)
        ) as cur:
            return await cur.fetchone() is not None


async def authorize(tg_id: int) -> None:
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (tg_id, authorized_at) VALUES (?, ?)",
            (tg_id, _now()),
        )
        await db.commit()


async def revoke(tg_id: int) -> bool:
    """Remove authorization. Returns True if a row was deleted."""
    async with aiosqlite.connect(_DB_PATH) as db:
        cur = await db.execute("DELETE FROM users WHERE tg_id = ?", (tg_id,))
        await db.commit()
        return cur.rowcount > 0


async def stats() -> dict[str, object]:
    async with aiosqlite.connect(_DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            count = row[0] if row else 0
        async with db.execute(
            "SELECT tg_id, authorized_at FROM users ORDER BY authorized_at DESC LIMIT 10"
        ) as cur:
            recent = await cur.fetchall()
    return {"total": count, "recent": [tuple(r) for r in recent]}
