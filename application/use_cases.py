"""
Application use cases.

This layer orchestrates domain objects and repository interfaces to fulfil
a specific user goal. It has no knowledge of SQLite, reportlab, or any
other infrastructure concern — those are injected as dependencies.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from domain.entities import Runner, Workout
from domain.repositories import RunnerRepository, WorkoutRepository, IntervalRepository
from domain.stats import WorkoutStats, compute_workout_stats


# ── Output port: what the use case needs from infrastructure ─────────────────

class ReportGenerator(Protocol):
    """Generates a report file for a single runner's workout."""

    def generate(
        self,
        runner: Runner,
        workout: Workout,
        stats: WorkoutStats,
    ) -> Path:
        """Produce a report and return the path to the created file."""
        ...


# ── Result types ─────────────────────────────────────────────────────────────

@dataclass
class RunnerReportResult:
    runner: Runner
    pdf_path: Path
    success: bool
    reason: str = ""


@dataclass
class GenerateReportsResult:
    results: list[RunnerReportResult]

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def total(self) -> int:
        return len(self.results)


# ── Use case ─────────────────────────────────────────────────────────────────

class GenerateReportsUseCase:
    """
    For each runner, fetch their latest workout, compute statistics,
    and produce a report file.

    Dependencies are injected so this class can be tested with fakes
    without touching the filesystem or database.
    """

    def __init__(
        self,
        runner_repo: RunnerRepository,
        workout_repo: WorkoutRepository,
        interval_repo: IntervalRepository,
        report_generator: ReportGenerator,
    ):
        self._runners = runner_repo
        self._workouts = workout_repo
        self._intervals = interval_repo
        self._generator = report_generator

    def execute(self, runner_id: int | None = None) -> GenerateReportsResult:
        """
        Generate reports for all runners, or for a single runner if
        runner_id is provided.
        """
        if runner_id is not None:
            runner = self._runners.get_by_id(runner_id)
            runners = [runner] if runner else []
        else:
            runners = self._runners.get_all()

        results = [self._process_runner(runner) for runner in runners]
        return GenerateReportsResult(results=results)

    def _process_runner(self, runner: Runner) -> RunnerReportResult:
        workout = self._workouts.get_latest_for_runner(runner.id)
        if not workout:
            return RunnerReportResult(
                runner=runner,
                pdf_path=Path(),
                success=False,
                reason="no workouts found",
            )

        intervals = self._intervals.get_for_workout(workout.id)
        if not intervals:
            return RunnerReportResult(
                runner=runner,
                pdf_path=Path(),
                success=False,
                reason="no intervals recorded for latest workout",
            )

        stats = compute_workout_stats(intervals)
        pdf_path = self._generator.generate(runner, workout, stats)

        return RunnerReportResult(
            runner=runner,
            pdf_path=pdf_path,
            success=True,
        )
