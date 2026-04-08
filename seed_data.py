"""
seed_data.py — Populate the database with sample runners and workouts.

Run once before demoing:
    python seed_data.py
"""

from infrastructure.sqlite_repository import init_db, _get_connection

RUNNERS = [
    ("Alice Mbeki",   "alice@example.com"),
    ("Carlos Ruiz",   "carlos@example.com"),
    ("Dana Park",     "dana@example.com"),
    ("James Okonkwo", "james@example.com"),
]

# (runner_name, workout_date, notes, [(interval_number, distance_m, duration_sec, rest_sec)])
WORKOUTS = [
    (
        "Alice Mbeki", "2025-04-01",
        "Felt strong, negative split on last two reps.",
        [(1,400,98.4,90),(2,400,96.1,90),(3,400,95.7,90),
         (4,400,94.2,90),(5,400,93.5,90),(6,400,92.8,0)],
    ),
    (
        "Carlos Ruiz", "2025-04-01",
        "Good effort. Struggled a bit on intervals 4 and 5.",
        [(1,400,105.2,90),(2,400,104.8,90),(3,400,103.9,90),
         (4,400,108.1,90),(5,400,107.6,90),(6,400,104.3,0)],
    ),
    (
        "Dana Park", "2025-04-01",
        "800m reps. Consistent throughout.",
        [(1,800,210.5,120),(2,800,209.1,120),
         (3,800,211.4,120),(4,800,208.7,0)],
    ),
    (
        "James Okonkwo", "2025-04-01",
        "First session back after injury. Controlled effort.",
        [(1,400,118.0,120),(2,400,116.5,120),
         (3,400,115.8,120),(4,400,114.2,0)],
    ),
]


def seed():
    init_db()

    with _get_connection() as conn:
        runner_ids = {}
        for name, email in RUNNERS:
            existing = conn.execute(
                "SELECT id FROM runners WHERE email = ?", (email,)
            ).fetchone()
            if existing:
                runner_ids[name] = existing["id"]
                print(f"  [skip] {name} already exists")
            else:
                cur = conn.execute(
                    "INSERT INTO runners (name, email) VALUES (?, ?)", (name, email)
                )
                runner_ids[name] = cur.lastrowid
                print(f"  [+] Runner: {name}")

        for runner_name, workout_date, notes, intervals in WORKOUTS:
            runner_id = runner_ids[runner_name]
            existing = conn.execute(
                "SELECT id FROM workouts WHERE runner_id = ? AND workout_date = ?",
                (runner_id, workout_date),
            ).fetchone()
            if existing:
                print(f"  [skip] Workout for {runner_name} on {workout_date} already exists")
                continue

            cur = conn.execute(
                "INSERT INTO workouts (runner_id, workout_date, notes) VALUES (?, ?, ?)",
                (runner_id, workout_date, notes),
            )
            workout_id = cur.lastrowid
            for num, dist, dur, rest in intervals:
                conn.execute(
                    """INSERT INTO intervals
                       (workout_id, interval_number, distance_meters, duration_seconds, rest_seconds)
                       VALUES (?, ?, ?, ?, ?)""",
                    (workout_id, num, dist, dur, rest),
                )
            print(f"  [+] Workout for {runner_name}: {len(intervals)} intervals")

    print("\nSeed complete.\n")


if __name__ == "__main__":
    seed()
