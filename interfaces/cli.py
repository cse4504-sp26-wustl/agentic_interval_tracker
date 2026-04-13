"""
Interfaces: command-line interface.

The only entry point for the application. Responsible for:
  - parsing arguments
  - constructing and injecting all dependencies
  - printing results to stdout

It knows about every layer, but nothing else does.
"""

import argparse
import sys

from infrastructure.sqlite_repository import (
    SqliteRunnerRepository,
    SqliteWorkoutRepository,
    SqliteIntervalRepository,
    SqlitePersonalBestRepository,
    init_db,
)
from infrastructure.pdf_generator import PdfReportGenerator
from application.use_cases import GenerateReportsUseCase


def build_use_case() -> GenerateReportsUseCase:
    """Construct the use case with all concrete dependencies wired in."""
    return GenerateReportsUseCase(
        runner_repo=SqliteRunnerRepository(),
        workout_repo=SqliteWorkoutRepository(),
        interval_repo=SqliteIntervalRepository(),
        personal_best_repo=SqlitePersonalBestRepository(),
        report_generator=PdfReportGenerator(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate interval training PDF reports."
    )
    parser.add_argument(
        "--runner-id", type=int, default=None,
        help="Generate report for a single runner (default: all runners)",
    )
    args = parser.parse_args()

    init_db()
    use_case = build_use_case()
    result = use_case.execute(runner_id=args.runner_id)

    if result.total == 0:
        print("\nNo runners found. Run seed_data.py to add sample data.\n")
        sys.exit(1)

    label = f"runner ID {args.runner_id}" if args.runner_id else f"{result.total} runner(s)"
    print(f"\nGenerating reports for {label}...\n")

    for r in result.results:
        if r.success:
            print(f"  [✓] {r.runner.name} → {r.pdf_path.name}")
            # Show personal bests if any were achieved
            if r.personal_bests:
                for pb in r.personal_bests:
                    if pb.is_improvement:
                        print(f"      🏆 NEW PB: {pb.description}")
                        if pb.previous_best:
                            from domain.stats import format_duration, format_pace
                            if 'pace' in pb.pb_type and pb.pb_type != 'avg_pace':
                                old_desc = format_duration(pb.previous_best)
                                improvement = pb.previous_best - pb.value
                                print(f"          (Previous: {old_desc}, improved by {format_duration(improvement)})")
                            elif pb.pb_type == 'avg_pace':
                                old_desc = format_pace(pb.previous_best)
                                print(f"          (Previous: {old_desc})")
                            else:  # distance
                                print(f"          (Previous: {int(pb.previous_best)}m)")
        else:
            print(f"  [!] {r.runner.name} — skipped ({r.reason})")

    print(f"\nDone. {result.success_count}/{result.total} reports generated in reports/\n")


if __name__ == "__main__":
    main()
