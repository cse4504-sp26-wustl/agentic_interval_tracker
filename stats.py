"""
Performance statistics calculated from raw interval data.
All pace values are in seconds per kilometer.
"""

from dataclasses import dataclass
from models import Interval


@dataclass
class IntervalStats:
    interval_number: int
    distance_meters: int
    duration_seconds: float
    rest_seconds: float
    pace_sec_per_km: float      # seconds per km for this interval


@dataclass
class WorkoutStats:
    total_distance_meters: int
    total_duration_seconds: float
    avg_pace_sec_per_km: float
    best_pace_sec_per_km: float
    worst_pace_sec_per_km: float
    intervals: list[IntervalStats]


def pace_sec_per_km(distance_meters: int, duration_seconds: float) -> float:
    """Return pace in seconds/km. Returns 0 if distance is 0."""
    if distance_meters == 0:
        return 0.0
    return (duration_seconds / distance_meters) * 1000


def format_pace(sec_per_km: float) -> str:
    """Format pace as mm:ss /km string, e.g. '4:32 /km'."""
    minutes, seconds = divmod(int(sec_per_km), 60)
    return f"{minutes}:{seconds:02d} /km"


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as m:ss, e.g. '2:05'."""
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"


def compute_workout_stats(intervals: list[Interval]) -> WorkoutStats:
    """Compute aggregate and per-interval statistics for a workout."""
    if not intervals:
        return WorkoutStats(
            total_distance_meters=0,
            total_duration_seconds=0,
            avg_pace_sec_per_km=0,
            best_pace_sec_per_km=0,
            worst_pace_sec_per_km=0,
            intervals=[],
        )

    interval_stats = [
        IntervalStats(
            interval_number=iv.interval_number,
            distance_meters=iv.distance_meters,
            duration_seconds=iv.duration_seconds,
            rest_seconds=iv.rest_seconds,
            pace_sec_per_km=pace_sec_per_km(iv.distance_meters, iv.duration_seconds),
        )
        for iv in intervals
    ]

    total_distance = sum(iv.distance_meters for iv in intervals)
    total_duration = sum(iv.duration_seconds for iv in intervals)
    paces = [s.pace_sec_per_km for s in interval_stats if s.pace_sec_per_km > 0]

    return WorkoutStats(
        total_distance_meters=total_distance,
        total_duration_seconds=total_duration,
        avg_pace_sec_per_km=sum(paces) / len(paces) if paces else 0,
        best_pace_sec_per_km=min(paces) if paces else 0,
        worst_pace_sec_per_km=max(paces) if paces else 0,
        intervals=interval_stats,
    )
