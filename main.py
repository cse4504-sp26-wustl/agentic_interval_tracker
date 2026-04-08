"""
main.py — Generate PDF reports for all runners after a workout session.

Usage:
    python main.py                  # generate reports for all runners
    python main.py --runner-id 3    # generate report for a single runner
"""

import argparse
import sys
from pathlib import Path

from models import init_db, get_all_runners, get_runner_by_id, get_latest_workout, get_intervals_for_workout
from stats import compute_workout_stats
from reports_generator import generate_report


def generate_for_runner(runner_id: int) -> bool:
    """Generate a PDF report for the given runner's latest workout.
    Returns True on success, False if no workout data found.
    """
    runner = get_runner_by_id(runner_id)
    if not runner:
        print(f"  [!] Runner ID {runner_id} not found.")
        return False

    workout = get_latest_workout(runner.id)
    if not workout:
        print(f"  [!] No workouts found for {runner.name}.")
        return False

    intervals = get_intervals_for_workout(workout.id)
    if not intervals:
        print(f"  [!] No intervals found for {runner.name}'s latest workout.")
        return False

    stats = compute_workout_stats(intervals)
    pdf_path = generate_report(runner, workout, stats)
    print(f"  [✓] {runner.name} → {pdf_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate interval training PDF reports."
    )
    parser.add_argument(
        "--runner-id", type=int, default=None,
        help="Generate report for a single runner (default: all runners)"
    )
    args = parser.parse_args()

    init_db()

    if args.runner_id:
        print(f"\nGenerating report for runner ID {args.runner_id}...\n")
        success = generate_for_runner(args.runner_id)
        sys.exit(0 if success else 1)
    else:
        runners = get_all_runners()
        if not runners:
            print("\nNo runners found. Run seed_data.py to add sample data.\n")
            sys.exit(1)

        print(f"\nGenerating reports for {len(runners)} runner(s)...\n")
        results = [generate_for_runner(r.id) for r in runners]
        success_count = sum(results)
        print(f"\nDone. {success_count}/{len(runners)} reports generated in reports/\n")


if __name__ == "__main__":
    main()
