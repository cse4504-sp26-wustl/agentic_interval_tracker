"""
Infrastructure: PDF report generator.

Implements the ReportGenerator protocol from the application layer
using reportlab. This is the only file that knows about reportlab.
"""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from domain.entities import Runner, Workout
from domain.stats import WorkoutStats, format_duration, format_pace

REPORTS_DIR = Path(__file__).parent.parent / "reports"

BRAND_DARK   = colors.HexColor("#1a1a2e")
BRAND_MID    = colors.HexColor("#16213e")
BRAND_ACCENT = colors.HexColor("#e94560")
ROW_ALT      = colors.HexColor("#f5f7fa")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "rpt_title", parent=base["Title"],
            fontSize=22, textColor=BRAND_DARK, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "rpt_subtitle", parent=base["Normal"],
            fontSize=11, textColor=colors.grey, spaceAfter=16,
        ),
        "section": ParagraphStyle(
            "rpt_section", parent=base["Heading2"],
            fontSize=13, textColor=BRAND_MID, spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "rpt_body", parent=base["Normal"],
            fontSize=10, leading=14,
        ),
        "note": ParagraphStyle(
            "rpt_note", parent=base["Normal"],
            fontSize=9, textColor=colors.grey, leading=13,
        ),
    }


def _summary_table(stats: WorkoutStats) -> Table:
    data = [
        ["Metric", "Value"],
        ["Total distance",    f"{stats.total_distance_meters:,} m"],
        ["Total work time",   format_duration(stats.total_duration_seconds)],
        ["Average pace",      format_pace(stats.avg_pace_sec_per_km)],
        ["Best interval",     format_pace(stats.best_pace_sec_per_km)],
        ["Slowest interval",  format_pace(stats.worst_pace_sec_per_km)],
        ["Intervals",         str(len(stats.intervals))],
    ]
    t = Table(data, colWidths=[7 * cm, 7 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), BRAND_MID),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("FONTSIZE",       (0, 1), (-1, -1), 10),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#dce0e8")),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
    ]))
    return t


def _interval_table(stats: WorkoutStats) -> Table:
    header = ["#", "Distance", "Time", "Pace", "Rest"]
    rows = [header] + [
        [
            str(iv.interval_number),
            f"{iv.distance_meters} m",
            format_duration(iv.duration_seconds),
            format_pace(iv.pace_sec_per_km),
            format_duration(iv.rest_seconds) if iv.rest_seconds else "—",
        ]
        for iv in stats.intervals
    ]
    col_w = [1.5 * cm, 3.5 * cm, 3 * cm, 4 * cm, 3 * cm]
    t = Table(rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), BRAND_ACCENT),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("FONTSIZE",       (0, 1), (-1, -1), 9),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#dce0e8")),
        ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
    ]))
    return t


class PdfReportGenerator:
    """
    Implements the ReportGenerator protocol.
    Generates a styled PDF for a single runner's workout.
    """

    def __init__(self, output_dir: Path = REPORTS_DIR):
        self._output_dir = output_dir

    def generate(self, runner: Runner, workout: Workout, stats: WorkoutStats) -> Path:
        self._output_dir.mkdir(exist_ok=True)
        filename = f"{runner.name.replace(' ', '_')}_{workout.workout_date}.pdf"
        output_path = self._output_dir / filename

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
        )

        s = _styles()
        story = [
            Paragraph("Interval Training Report", s["title"]),
            Paragraph(f"{runner.name} &nbsp;·&nbsp; {workout.workout_date}", s["subtitle"]),
            HRFlowable(width="100%", thickness=1, color=BRAND_ACCENT),
            Spacer(1, 0.4 * cm),
            Paragraph("Workout Summary", s["section"]),
            _summary_table(stats),
            Spacer(1, 0.5 * cm),
            Paragraph("Interval Breakdown", s["section"]),
            _interval_table(stats),
            Spacer(1, 0.4 * cm),
        ]

        if workout.notes:
            story += [
                Paragraph("Coach Notes", s["section"]),
                Paragraph(workout.notes, s["body"]),
                Spacer(1, 0.3 * cm),
            ]

        story += [
            Spacer(1, 0.5 * cm),
            HRFlowable(width="100%", thickness=0.5, color=colors.grey),
            Paragraph(
                f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                s["note"],
            ),
        ]

        doc.build(story)
        return output_path
