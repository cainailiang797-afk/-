"""SQLite 项目元数据 + 任务队列。"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    with get_conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                name          TEXT PRIMARY KEY,
                topic         TEXT,
                json_path     TEXT NOT NULL,
                video_path    TEXT,
                poster_path   TEXT,
                vertical      INTEGER DEFAULT 1,
                status        TEXT DEFAULT 'idle',  -- idle / generating / done / error
                error         TEXT,
                created_at    REAL NOT NULL,
                updated_at    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id            TEXT PRIMARY KEY,
                project_name  TEXT NOT NULL,
                kind          TEXT NOT NULL,  -- generate / generate_json
                status        TEXT DEFAULT 'pending',  -- pending / running / done / error
                log           TEXT DEFAULT '',
                created_at    REAL NOT NULL,
                updated_at    REAL NOT NULL,
                FOREIGN KEY (project_name) REFERENCES projects(name) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                key           TEXT PRIMARY KEY,
                value         TEXT
            );
            """
        )


# --- projects ---------------------------------------------------------------

def upsert_project(name: str, topic: str, json_path: str,
                   vertical: int = 1) -> dict[str, Any]:
    now = time.time()
    with get_conn() as c:
        c.execute(
            """INSERT INTO projects (name, topic, json_path, vertical, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                 topic = excluded.topic,
                 json_path = excluded.json_path,
                 vertical = excluded.vertical,
                 updated_at = excluded.updated_at""",
            (name, topic, json_path, vertical, now, now),
        )
    return get_project(name)


def set_project_status(name: str, status: str, error: str | None = None,
                       video_path: str | None = None) -> None:
    fields = ["status = ?", "updated_at = ?", "error = ?"]
    vals: list[Any] = [status, time.time(), error]
    if video_path is not None:
        fields.append("video_path = ?")
        vals.append(video_path)
    vals.append(name)
    with get_conn() as c:
        c.execute(f"UPDATE projects SET {', '.join(fields)} WHERE name = ?", vals)


def list_projects() -> list[dict[str, Any]]:
    with get_conn() as c:
        rows = c.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_project(name: str) -> dict[str, Any] | None:
    with get_conn() as c:
        r = c.execute("SELECT * FROM projects WHERE name = ?", (name,)).fetchone()
    return dict(r) if r else None


def delete_project(name: str) -> None:
    with get_conn() as c:
        c.execute("DELETE FROM projects WHERE name = ?", (name,))


# --- jobs -------------------------------------------------------------------

def create_job(job_id: str, project_name: str, kind: str) -> None:
    now = time.time()
    with get_conn() as c:
        c.execute(
            "INSERT INTO jobs (id, project_name, kind, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'pending', ?, ?)",
            (job_id, project_name, kind, now, now),
        )


def update_job(job_id: str, status: str | None = None, log: str | None = None) -> None:
    fields, vals = ["updated_at = ?"], [time.time()]
    if status is not None:
        fields.append("status = ?")
        vals.append(status)
    if log is not None:
        fields.append("log = ?")
        vals.append(log)
    vals.append(job_id)
    with get_conn() as c:
        c.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?", vals)


def get_job(job_id: str) -> dict[str, Any] | None:
    with get_conn() as c:
        r = c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(r) if r else None


def append_job_log(job_id: str, line: str) -> None:
    with get_conn() as c:
        c.execute("UPDATE jobs SET log = log || ?, updated_at = ? WHERE id = ?",
                  (line + "\n", time.time(), job_id))


# --- settings ---------------------------------------------------------------

def get_setting(key: str) -> str | None:
    with get_conn() as c:
        r = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return r["value"] if r else None


def set_setting(key: str, value: str) -> None:
    with get_conn() as c:
        c.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
