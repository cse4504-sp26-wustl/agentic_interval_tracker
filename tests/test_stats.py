"""
Tests for domain statistics.

Because domain/stats.py is pure functions with no I/O,
these tests need no database, no filesystem, no mocking.

Run with:
    python -m pytest tests/ -v
"""

import pytest
from domain.entities import Interval
from domain.stats import (
    compute_workout_stats,
    format_duration,
    format_pace,
    pace_sec_per_km,
)


def make_interval(num: int, dist: int, dur: float, rest: float = 60.0) -> Interval:
    return Interval(
        id=num,
        workout_id=1,
        interval_number=num,
        distance_meters=dist,
        duration_seconds=dur,
        rest_seconds=rest,
    )


class TestPaceCalculations:
    def test_pace_400m(self):
        assert pace_sec_per_km(400, 96) == pytest.approx(240.0)

    def test_pace_800m(self):
        assert pace_sec_per_km(800, 240) == pytest.approx(300.0)

    def test_pace_zero_distance(self):
        assert pace_sec_per_km(0, 60) == 0.0

    def test_format_pace_round(self):
        assert format_pace(240.0) == "4:00 /km"

    def test_format_pace_with_seconds(self):
        assert format_pace(273.0) == "4:33 /km"

    def test_format_duration(self):
        assert format_duration(96) == "1:36"

    def test_format_duration_exact_minutes(self):
        assert format_duration(120) == "2:00"


class TestWorkoutStats:
    def test_empty_intervals_returns_zeros(self):
        stats = compute_workout_stats([])
        assert stats.total_distance_meters == 0
        assert stats.total_duration_seconds == 0.0
        assert stats.intervals == ()

    def test_total_distance(self):
        intervals = [make_interval(i, 400, 96) for i in range(1, 5)]
        stats = compute_workout_stats(intervals)
        assert stats.total_distance_meters == 1600

    def test_total_duration(self):
        intervals = [make_interval(1, 400, 90), make_interval(2, 400, 96)]
        stats = compute_workout_stats(intervals)
        assert stats.total_duration_seconds == 186.0

    def test_best_pace_is_fastest(self):
        intervals = [
            make_interval(1, 400, 90),   # 225 sec/km — faster
            make_interval(2, 400, 100),  # 250 sec/km — slower
        ]
        stats = compute_workout_stats(intervals)
        assert stats.best_pace_sec_per_km == pytest.approx(225.0)

    def test_worst_pace_is_slowest(self):
        intervals = [
            make_interval(1, 400, 90),
            make_interval(2, 400, 100),
        ]
        stats = compute_workout_stats(intervals)
        assert stats.worst_pace_sec_per_km == pytest.approx(250.0)

    def test_avg_pace(self):
        intervals = [
            make_interval(1, 400, 80),   # 200 sec/km
            make_interval(2, 400, 120),  # 300 sec/km
        ]
        stats = compute_workout_stats(intervals)
        assert stats.avg_pace_sec_per_km == pytest.approx(250.0)

    def test_interval_count(self):
        intervals = [make_interval(i, 400, 96) for i in range(1, 7)]
        stats = compute_workout_stats(intervals)
        assert len(stats.intervals) == 6

    def test_stats_are_immutable(self):
        """WorkoutStats and IntervalStats are frozen dataclasses."""
        intervals = [make_interval(1, 400, 96)]
        stats = compute_workout_stats(intervals)
        with pytest.raises((AttributeError, TypeError)):
            stats.total_distance_meters = 999  # type: ignore
