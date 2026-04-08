"""
Domain repository interfaces.

Abstract base classes that define the data-access contract the application
layer depends on. Infrastructure provides concrete implementations.

The application layer imports only these abstractions — never sqlite3,
never any specific database driver.
"""

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities import Runner, Workout, Interval


class RunnerRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[Runner]:
        """Return all runners, ordered by name."""
        ...

    @abstractmethod
    def get_by_id(self, runner_id: int) -> Optional[Runner]:
        """Return a runner by primary key, or None if not found."""
        ...


class WorkoutRepository(ABC):
    @abstractmethod
    def get_latest_for_runner(self, runner_id: int) -> Optional[Workout]:
        """Return the most recent workout for the given runner, or None."""
        ...

    @abstractmethod
    def get_all_for_runner(self, runner_id: int) -> list[Workout]:
        """Return all workouts for the given runner, newest first."""
        ...


class IntervalRepository(ABC):
    @abstractmethod
    def get_for_workout(self, workout_id: int) -> list[Interval]:
        """Return all intervals for the given workout, ordered by interval_number."""
        ...
