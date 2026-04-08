"""
Database models for the interval training tracker.
Uses SQLite via Python's built-in sqlite3 module.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "tracker.db"


@dataclass
class Runner:
    id: int
    name: str
    email: str
    created_at: str


@dataclass
class Workout:
    id: int
    runner_id: int
    workout_date: str
    notes: Optional[str]


@dataclass
class Interval:
    id: int
    workout_id: int
    interval_number: int
    distance_meters: int
    duration_seconds: float
    rest_seconds: float


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runners (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                email       TEXT    NOT NULL UNIQUE,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS workouts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                runner_id    INTEGER NOT NULL REFERENCES runners(id),
                workout_date TEXT    NOT NULL,
                notes        TEXT
            );

            CREATE TABLE IF NOT EXISTS intervals (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id      INTEGER NOT NULL REFERENCES workouts(id),
                interval_number INTEGER NOT NULL,
                distance_meters INTEGER NOT NULL,
                duration_seconds REAL   NOT NULL,
                rest_seconds    REAL    NOT NULL DEFAULT 0
            );
        """)


# ── Runner queries ────────────────────────────────────────────────────────────

def get_all_runners() -> list[Runner]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM runners ORDER BY name").fetchall()
    return [Runner(**dict(r)) for r in rows]


def get_runner_by_id(runner_id: int) -> Optional[Runner]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM runners WHERE id = ?", (runner_id,)
        ).fetchone()
    return Runner(**dict(row)) if row else None


# ── Workout queries ───────────────────────────────────────────────────────────

def get_workouts_for_runner(runner_id: int) -> list[Workout]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM workouts WHERE runner_id = ? ORDER BY workout_date DESC",
            (runner_id,),
        ).fetchall()
    return [Workout(**dict(r)) for r in rows]


def get_latest_workout(runner_id: int) -> Optional[Workout]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM workouts WHERE runner_id = ? ORDER BY workout_date DESC LIMIT 1",
            (runner_id,),
        ).fetchone()
    return Workout(**dict(row)) if row else None


# ── Interval queries ──────────────────────────────────────────────────────────

def get_intervals_for_workout(workout_id: int) -> list[Interval]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM intervals WHERE workout_id = ? ORDER BY interval_number",
            (workout_id,),
        ).fetchall()
    return [Interval(**dict(r)) for r in rows]
