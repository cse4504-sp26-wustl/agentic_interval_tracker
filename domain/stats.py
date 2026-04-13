"""
Domain statistics.

Pure functions that compute performance metrics from domain entities.
No I/O, no framework dependencies — easy to test in isolation.
"""

from dataclasses import dataclass
from domain.entities import Interval, PersonalBest


@dataclass(frozen=True)
class PersonalBestRecord:
    """Represents a newly achieved personal best."""
    pb_type: str
    value: float
    description: str
    previous_best: float | None = None

    @property
    def is_improvement(self) -> bool:
        return self.previous_best is None or self.value < self.previous_best


@dataclass(frozen=True)
class IntervalStats:
    interval_number: int
    distance_meters: int
    duration_seconds: float
    rest_seconds: float
    pace_sec_per_km: float


@dataclass(frozen=True)
class WorkoutStats:
    total_distance_meters: int
    total_duration_seconds: float
    avg_pace_sec_per_km: float
    best_pace_sec_per_km: float
    worst_pace_sec_per_km: float
    intervals: tuple[IntervalStats, ...]


def pace_sec_per_km(distance_meters: int, duration_seconds: float) -> float:
    """Pace in seconds/km. Returns 0.0 if distance is zero."""
    if distance_meters == 0:
        return 0.0
    return (duration_seconds / distance_meters) * 1000


def format_pace(sec_per_km: float) -> str:
    """Format pace as 'm:ss /km', e.g. '4:32 /km'."""
    minutes, seconds = divmod(int(sec_per_km), 60)
    return f"{minutes}:{seconds:02d} /km"


def format_duration(seconds: float) -> str:
    """Format a duration as 'm:ss', e.g. '1:36'."""
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"


def compute_workout_stats(intervals: list[Interval]) -> WorkoutStats:
    """Compute aggregate and per-interval statistics from a list of intervals."""
    if not intervals:
        return WorkoutStats(
            total_distance_meters=0,
            total_duration_seconds=0.0,
            avg_pace_sec_per_km=0.0,
            best_pace_sec_per_km=0.0,
            worst_pace_sec_per_km=0.0,
            intervals=(),
        )

    interval_stats = tuple(
        IntervalStats(
            interval_number=iv.interval_number,
            distance_meters=iv.distance_meters,
            duration_seconds=iv.duration_seconds,
            rest_seconds=iv.rest_seconds,
            pace_sec_per_km=pace_sec_per_km(iv.distance_meters, iv.duration_seconds),
        )
        for iv in intervals
    )

    total_distance = sum(iv.distance_meters for iv in intervals)
    total_duration = sum(iv.duration_seconds for iv in intervals)
    paces = [s.pace_sec_per_km for s in interval_stats if s.pace_sec_per_km > 0]

    return WorkoutStats(
        total_distance_meters=total_distance,
        total_duration_seconds=total_duration,
        avg_pace_sec_per_km=sum(paces) / len(paces) if paces else 0.0,
        best_pace_sec_per_km=min(paces) if paces else 0.0,
        worst_pace_sec_per_km=max(paces) if paces else 0.0,
        intervals=interval_stats,
    )


def detect_personal_bests(intervals: list[Interval], stats: WorkoutStats, 
                         existing_bests: dict[str, PersonalBest]) -> list[PersonalBestRecord]:
    """
    Detect personal bests from workout data.
    
    Args:
        intervals: List of intervals from the workout
        stats: Computed workout statistics
        existing_bests: Dict of pb_type -> PersonalBest for current records
    
    Returns:
        List of newly achieved personal best records
    """
    new_bests = []
    
    # Check distance-based pace records
    distance_totals = {}
    distance_times = {}
    
    # Aggregate intervals by distance to find best times
    for interval in intervals:
        dist = interval.distance_meters
        if dist not in distance_totals:
            distance_totals[dist] = 0
            distance_times[dist] = 0
        distance_totals[dist] += dist
        distance_times[dist] += interval.duration_seconds
    
    # Check for pace PBs at common distances
    for distance_meters in [400, 800, 1600, 5000]:
        if distance_meters in distance_times:
            time = distance_times[distance_meters]
            pb_type = f"pace_{distance_meters}m"
            existing = existing_bests.get(pb_type)
            existing_time = existing.value if existing else None
            
            if existing_time is None or time < existing_time:
                new_bests.append(PersonalBestRecord(
                    pb_type=pb_type,
                    value=time,
                    description=f"{distance_meters}m in {format_duration(time)}",
                    previous_best=existing_time
                ))
    
    # Check total distance PB
    total_dist = stats.total_distance_meters
    if total_dist > 0:
        existing_dist = existing_bests.get("total_distance")
        existing_value = existing_dist.value if existing_dist else None
        
        if existing_value is None or total_dist > existing_value:
            new_bests.append(PersonalBestRecord(
                pb_type="total_distance",
                value=float(total_dist),
                description=f"Total distance: {total_dist}m",
                previous_best=existing_value
            ))
    
    # Check average pace PB (lower is better for pace)
    if stats.avg_pace_sec_per_km > 0:
        existing_pace = existing_bests.get("avg_pace")
        existing_value = existing_pace.value if existing_pace else None
        
        if existing_value is None or stats.avg_pace_sec_per_km < existing_value:
            new_bests.append(PersonalBestRecord(
                pb_type="avg_pace",
                value=stats.avg_pace_sec_per_km,
                description=f"Average pace: {format_pace(stats.avg_pace_sec_per_km)}",
                previous_best=existing_value
            ))
    
    return new_bests
