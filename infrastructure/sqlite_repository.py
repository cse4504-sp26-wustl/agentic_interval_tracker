"""
Infrastructure: SQLite repository implementations.

Concrete implementations of the domain repository interfaces using
Python's built-in sqlite3. This is the only file that knows about
the database schema and SQL.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from domain.entities import Runner, Workout, Interval, PersonalBest
from domain.repositories import RunnerRepository, WorkoutRepository, IntervalRepository, PersonalBestRepository

DB_PATH = Path(__file__).parent.parent / "data" / "tracker.db"


def _get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """Create tables if they don't exist."""
    with _get_connection(db_path) as conn:
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
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id       INTEGER NOT NULL REFERENCES workouts(id),
                interval_number  INTEGER NOT NULL,
                distance_meters  INTEGER NOT NULL,
                duration_seconds REAL    NOT NULL,
                rest_seconds     REAL    NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS personal_bests (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                runner_id     INTEGER NOT NULL REFERENCES runners(id),
                pb_type       TEXT    NOT NULL,
                value         REAL    NOT NULL,
                workout_id    INTEGER NOT NULL REFERENCES workouts(id),
                achieved_date TEXT    NOT NULL,
                previous_best REAL,
                UNIQUE(runner_id, pb_type)
            );
        """)


class SqliteRunnerRepository(RunnerRepository):
    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path

    def get_all(self) -> list[Runner]:
        with _get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM runners ORDER BY name"
            ).fetchall()
        return [Runner(**dict(r)) for r in rows]

    def get_by_id(self, runner_id: int) -> Optional[Runner]:
        with _get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM runners WHERE id = ?", (runner_id,)
            ).fetchone()
        return Runner(**dict(row)) if row else None


class SqliteWorkoutRepository(WorkoutRepository):
    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path

    def get_latest_for_runner(self, runner_id: int) -> Optional[Workout]:
        with _get_connection(self._db_path) as conn:
            row = conn.execute(
                """SELECT * FROM workouts
                   WHERE runner_id = ?
                   ORDER BY workout_date DESC
                   LIMIT 1""",
                (runner_id,),
            ).fetchone()
        return Workout(**dict(row)) if row else None

    def get_all_for_runner(self, runner_id: int) -> list[Workout]:
        with _get_connection(self._db_path) as conn:
            rows = conn.execute(
                """SELECT * FROM workouts
                   WHERE runner_id = ?
                   ORDER BY workout_date DESC""",
                (runner_id,),
            ).fetchall()
        return [Workout(**dict(r)) for r in rows]


class SqliteIntervalRepository(IntervalRepository):
    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path

    def get_for_workout(self, workout_id: int) -> list[Interval]:
        with _get_connection(self._db_path) as conn:
            rows = conn.execute(
                """SELECT * FROM intervals
                   WHERE workout_id = ?
                   ORDER BY interval_number""",
                (workout_id,),
            ).fetchall()
        return [Interval(**dict(r)) for r in rows]


class SqlitePersonalBestRepository(PersonalBestRepository):
    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path

    def get_best_for_runner(self, runner_id: int, pb_type: str) -> Optional[PersonalBest]:
        with _get_connection(self._db_path) as conn:
            row = conn.execute(
                """SELECT * FROM personal_bests 
                   WHERE runner_id = ? AND pb_type = ?""",
                (runner_id, pb_type),
            ).fetchone()
        return PersonalBest(**dict(row)) if row else None

    def get_all_for_runner(self, runner_id: int) -> list[PersonalBest]:
        with _get_connection(self._db_path) as conn:
            rows = conn.execute(
                """SELECT * FROM personal_bests 
                   WHERE runner_id = ? 
                   ORDER BY achieved_date DESC""",
                (runner_id,),
            ).fetchall()
        return [PersonalBest(**dict(r)) for r in rows]

    def save(self, personal_best: PersonalBest) -> PersonalBest:
        with _get_connection(self._db_path) as conn:
            if personal_best.id == 0:  # New record
                cursor = conn.execute(
                    """INSERT OR REPLACE INTO personal_bests 
                       (runner_id, pb_type, value, workout_id, achieved_date, previous_best)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        personal_best.runner_id,
                        personal_best.pb_type,
                        personal_best.value,
                        personal_best.workout_id,
                        personal_best.achieved_date,
                        personal_best.previous_best,
                    ),
                )
                # Return new record with assigned ID
                return PersonalBest(
                    id=cursor.lastrowid,
                    runner_id=personal_best.runner_id,
                    pb_type=personal_best.pb_type,
                    value=personal_best.value,
                    workout_id=personal_best.workout_id,
                    achieved_date=personal_best.achieved_date,
                    previous_best=personal_best.previous_best,
                )
            else:  # Update existing
                conn.execute(
                    """UPDATE personal_bests 
                       SET value = ?, workout_id = ?, achieved_date = ?, previous_best = ?
                       WHERE id = ?""",
                    (
                        personal_best.value,
                        personal_best.workout_id,
                        personal_best.achieved_date,
                        personal_best.previous_best,
                        personal_best.id,
                    ),
                )
                return personal_best
