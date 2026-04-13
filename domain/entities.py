"""
Domain entities.

Pure data classes — no imports from any other layer, no I/O, no frameworks.
These are the core objects the entire application reasons about.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Runner:
    id: int
    name: str
    email: str
    created_at: str


@dataclass(frozen=True)
class Workout:
    id: int
    runner_id: int
    workout_date: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class Interval:
    id: int
    workout_id: int
    interval_number: int
    distance_meters: int
    duration_seconds: float
    rest_seconds: float = 0.0


@dataclass(frozen=True)
class PersonalBest:
    id: int
    runner_id: int
    pb_type: str  # e.g., 'pace_400m', 'pace_800m', 'total_distance', 'avg_pace'
    value: float  # time in seconds for pace, meters for distance
    workout_id: int
    achieved_date: str
    previous_best: Optional[float] = None
