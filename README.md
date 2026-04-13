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
│   └── use_cases.py         #   GenerateReportsUseCase, EmailReportsUseCase
│
├── infrastructure/          # Concrete implementations
│   ├── sqlite_repository.py #   SQLite implementations of domain interfaces
│   ├── pdf_generator.py     #   reportlab PDF generation
│   └── email_sender.py      #   SMTP email delivery
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

# 5. Generate reports AND email them to runners
python -m interfaces.cli --send-email

# 6. Test email delivery without actually sending
python -m interfaces.cli --send-email --dry-run
```

Reports are written to `reports/`, named `<Runner_Name>_<date>.pdf`.

## Email Delivery

The application can email PDF reports to runners via SMTP. Configure email delivery using environment variables:

### Required Environment Variables

```bash
SMTP_HOST=smtp.gmail.com          # SMTP server hostname
SMTP_USERNAME=your@email.com     # Email username for authentication
SMTP_PASSWORD=your-password       # Email password or app-specific password
```

### Optional Environment Variables

```bash
SMTP_PORT=587                     # SMTP port (default: 587)
SMTP_FROM_EMAIL=your@email.com   # From address (default: uses SMTP_USERNAME)
```

### Email Options

- `--send-email`: Send PDF reports via email after generation
- `--dry-run`: Simulate email sending without actually sending emails (requires `--send-email`)

### Example Email Configuration

For Gmail with app-specific password:
```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
```

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
