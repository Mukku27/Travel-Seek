from datetime import date

from export_utils import build_calendar_export, build_markdown_export, build_pdf_export

SAMPLE_PLAN = """
## Day 1: Arrival
- 9:00 AM Louvre Museum - Rating 4.8 - 2 hours - $30
- 1:00 PM Seine River Cruise - Rating 4.6 - 90 minutes - $25

## Local Tips
Carry small cash for cafes.
"""


def test_markdown_export_returns_plan_text():
    assert build_markdown_export(SAMPLE_PLAN) == SAMPLE_PLAN


def test_calendar_export_contains_ical_event_markers():
    payload = build_calendar_export("Paris", SAMPLE_PLAN, date(2026, 6, 1)).decode("utf-8")
    assert "BEGIN:VCALENDAR" in payload
    assert "SUMMARY:Louvre Museum" in payload


def test_pdf_export_returns_nonempty_bytes():
    payload = build_pdf_export(
        "Paris",
        SAMPLE_PLAN,
        date(2026, 6, 1),
        date(2026, 6, 3),
        "Moderate",
        ["Culture"],
    )
    assert payload.startswith(b"%PDF")
    assert len(payload) > 500
