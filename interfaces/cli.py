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
    init_db,
)
from infrastructure.pdf_generator import PdfReportGenerator
from infrastructure.email_sender import EmailSender, SMTPConfigError
from application.use_cases import GenerateReportsUseCase, EmailReportsUseCase


def build_report_use_case() -> GenerateReportsUseCase:
    """Construct the report generation use case with all concrete dependencies wired in."""
    return GenerateReportsUseCase(
        runner_repo=SqliteRunnerRepository(),
        workout_repo=SqliteWorkoutRepository(),
        interval_repo=SqliteIntervalRepository(),
        report_generator=PdfReportGenerator(),
    )


def build_email_use_case(dry_run: bool = False) -> EmailReportsUseCase:
    """Construct the email use case with all concrete dependencies wired in."""
    return EmailReportsUseCase(
        runner_repo=SqliteRunnerRepository(),
        email_sender=EmailSender(dry_run=dry_run),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate interval training PDF reports and optionally email them."
    )
    parser.add_argument(
        "--runner-id", type=int, default=None,
        help="Generate report for a single runner (default: all runners)",
    )
    parser.add_argument(
        "--send-email", action="store_true",
        help="Send PDF reports via email after generation",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate email sending without actually sending emails (requires --send-email)",
    )
    args = parser.parse_args()

    if args.dry_run and not args.send_email:
        print("Error: --dry-run can only be used with --send-email")
        sys.exit(1)

    init_db()
    
    # Always generate reports first
    report_use_case = build_report_use_case()
    result = report_use_case.execute(runner_id=args.runner_id)

    if result.total == 0:
        print("\nNo runners found. Run seed_data.py to add sample data.\n")
        sys.exit(1)

    label = f"runner ID {args.runner_id}" if args.runner_id else f"{result.total} runner(s)"
    print(f"\nGenerating reports for {label}...\n")

    for r in result.results:
        if r.success:
            print(f"  [✓] {r.runner.name} → {r.pdf_path.name}")
        else:
            print(f"  [!] {r.runner.name} — skipped ({r.reason})")

    print(f"\nDone. {result.success_count}/{result.total} reports generated in reports/")

    # Send emails if requested
    if args.send_email:
        try:
            email_use_case = build_email_use_case(dry_run=args.dry_run)
            email_result = email_use_case.execute(runner_id=args.runner_id)
            
            action = "Simulating email delivery" if args.dry_run else "Sending emails"
            print(f"\n{action} for {email_result.total} runner(s)...\n")
            
            for r in email_result.results:
                if r.email_sent:
                    action_verb = "simulated" if args.dry_run else "sent"
                    print(f"  [✓] {r.runner.name} ({r.runner.email}) — email {action_verb}")
                else:
                    print(f"  [!] {r.runner.name} ({r.runner.email}) — {r.reason}")
            
            action_verb = "would be sent" if args.dry_run else "sent"
            print(f"\nEmail summary: {email_result.success_count}/{email_result.total} emails {action_verb}")
            
        except SMTPConfigError as e:
            print(f"\nEmail configuration error: {e}")
            print("\nRequired environment variables:")
            print("  SMTP_HOST - SMTP server hostname")
            print("  SMTP_USERNAME - Username for authentication") 
            print("  SMTP_PASSWORD - Password for authentication")
            print("  SMTP_PORT - SMTP server port (optional, default: 587)")
            print("  SMTP_FROM_EMAIL - From email address (optional, defaults to username)")
            sys.exit(1)
        except Exception as e:
            print(f"\nUnexpected error during email sending: {e}")
            sys.exit(1)

    print()


if __name__ == "__main__":
    main()
