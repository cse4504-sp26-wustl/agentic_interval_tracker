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


# ── Output ports: what the use cases need from infrastructure ───────────────

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


class EmailSender(Protocol):
    """Sends emails with PDF attachments."""
    
    def send_report(
        self,
        to_email: str,
        runner_name: str,
        pdf_path: Path,
        subject: str | None = None,
    ) -> bool:
        """Send a PDF report as an email attachment. Returns True if successful."""
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


@dataclass
class EmailResult:
    runner: Runner
    pdf_path: Path
    email_sent: bool
    reason: str = ""


@dataclass
class EmailReportsResult:
    results: list[EmailResult]

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.email_sent)

    @property
    def total(self) -> int:
        return len(self.results)


# ── Use cases ────────────────────────────────────────────────────────────────

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


class EmailReportsUseCase:
    """
    Send PDF reports to runners via email.
    
    This use case finds existing PDF reports and emails them to the corresponding runners.
    It skips runners whose PDF reports are missing.
    """

    def __init__(
        self,
        runner_repo: RunnerRepository,
        email_sender: EmailSender,
        reports_dir: Path = Path("reports"),
    ):
        self._runners = runner_repo
        self._email_sender = email_sender
        self._reports_dir = reports_dir

    def execute(self, runner_id: int | None = None) -> EmailReportsResult:
        """
        Email reports to all runners, or for a single runner if runner_id is provided.
        Only sends emails for runners who have existing PDF reports.
        """
        if runner_id is not None:
            runner = self._runners.get_by_id(runner_id)
            runners = [runner] if runner else []
        else:
            runners = self._runners.get_all()

        results = [self._process_runner_email(runner) for runner in runners]
        return EmailReportsResult(results=results)

    def _process_runner_email(self, runner: Runner) -> EmailResult:
        # Find the runner's most recent PDF report
        pdf_path = self._find_runner_pdf(runner)
        
        if not pdf_path or not pdf_path.exists():
            return EmailResult(
                runner=runner,
                pdf_path=pdf_path or Path(),
                email_sent=False,
                reason="PDF report not found",
            )

        # Send the email
        success = self._email_sender.send_report(
            to_email=runner.email,
            runner_name=runner.name,
            pdf_path=pdf_path,
        )

        return EmailResult(
            runner=runner,
            pdf_path=pdf_path,
            email_sent=success,
            reason="" if success else "Failed to send email",
        )

    def _find_runner_pdf(self, runner: Runner) -> Path | None:
        """Find the most recent PDF report for a runner."""
        # PDF files are named like "Alice_Mbeki_2025-04-01.pdf"
        # We'll look for files that start with the runner's name (with spaces replaced by underscores)
        runner_name_pattern = runner.name.replace(" ", "_")
        
        # Find all PDFs for this runner
        matching_files = list(self._reports_dir.glob(f"{runner_name_pattern}_*.pdf"))
        
        if not matching_files:
            return None
        
        # Return the most recent one (by modification time)
        return max(matching_files, key=lambda f: f.stat().st_mtime)
