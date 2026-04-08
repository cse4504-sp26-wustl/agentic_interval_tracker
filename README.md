# Interval Training Tracker

A Python application that records runners' interval workout data and generates
PDF performance reports. Built with clean architecture.

## Architecture

```
interval-tracker/
├── domain/                  # Core business logic — no I/O, no frameworks
│   ├── entities.py          #   Runner, Workout, Interval dataclasses
│   ├── stats.py             #   Pure functions: pace, duration, aggregates
│   └── repositories.py      #   Abstract interfaces for data access
│
├── application/             # Use cases — orchestrates domain objects
│   └── use_cases.py         #   GenerateReportsUseCase
│
├── infrastructure/          # Concrete implementations
│   ├── sqlite_repository.py #   SQLite implementations of domain interfaces
│   └── pdf_generator.py     #   reportlab PDF generation
│
├── interfaces/              # Entry points
│   └── cli.py               #   argparse CLI, wires all dependencies together
│
├── seed_data.py             # Populate DB with sample data
├── requirements.txt
└── tests/
    └── test_stats.py        # Pure domain logic tests — no I/O needed
```

**Dependency rule:** `domain` ← `application` ← `infrastructure` / `interfaces`.
Inner layers never import from outer layers.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed the database
python seed_data.py

# 3. Generate PDF reports for all runners
python -m interfaces.cli

# 4. Or for a single runner
python -m interfaces.cli --runner-id 1
```

Reports are written to `reports/`, named `<Runner_Name>_<date>.pdf`.

## Running Tests

```bash
python -m pytest tests/ -v
```

## Data Model

```
runners        id, name, email, created_at
workouts       id, runner_id, workout_date, notes
intervals      id, workout_id, interval_number,
               distance_meters, duration_seconds, rest_seconds
```

## What's Missing (Your Task)

After generating reports the app has no delivery mechanism.
**The next feature is email delivery:** send each runner their PDF report
as an email attachment via SMTP.

Where it fits in the architecture:
- `infrastructure/email_sender.py` — SMTP implementation
- `application/use_cases.py` — a new `EmailReportsUseCase` (or extend the existing one)
- `interfaces/cli.py` — add a `--send-email` flag

Things to consider:
- SMTP config (host, port, credentials) should come from environment variables
- Each runner already has an `email` field
- PDFs are already in `reports/` by the time email runs
- Skip runners whose report file is missing
- Add a `--dry-run` flag that logs without sending
