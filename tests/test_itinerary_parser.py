"""Tests for itinerary markdown parsing helpers."""

from ui.itinerary_parser import parse_itinerary_markdown, parse_stop_line


def test_parse_stop_line_extracts_metadata_and_time():
    line = (
        "- 9:00 AM-11:00 AM: Visit Louvre Museum | duration: 2 hours | rating: 4.8 "
        "| cost: $35 | distance to next: 1.4 km"
    )
    stop = parse_stop_line(line)
    assert stop is not None
    assert stop.name == "Visit Louvre Museum"
    assert stop.time == "9:00 AM-11:00 AM"
    assert stop.duration == "2 hours"
    assert stop.rating == "4.8"
    assert stop.cost_estimate == "$35"
    assert stop.distance_to_next == "1.4 km"


def test_parse_stop_line_extracts_coordinates_when_present():
    line = "- 14:00: Explore Senso-ji Temple (35.7148, 139.7967) | rating: 4.7"
    stop = parse_stop_line(line)
    assert stop is not None
    assert stop.latitude == 35.7148
    assert stop.longitude == 139.7967
    assert stop.rating == "4.7"


def test_parse_itinerary_markdown_builds_day_sections():
    markdown = """
## Day 1: Historic Core
- 09:00-11:00: Visit Colosseum | duration: 2h | rating: 4.8 | cost: EUR 30 | distance to next: 2 km
- 12:00-13:30: Lunch in Monti | duration: 90 min | cost: EUR 25

## Day 2: Museums
- 10:00-12:30: Vatican Museums | duration: 2.5h | rating: 4.7 | cost: EUR 35
"""
    day_plans = parse_itinerary_markdown(markdown)
    assert len(day_plans) == 2
    assert day_plans[0].day_number == 1
    assert day_plans[0].title == "Historic Core"
    assert len(day_plans[0].stops) == 2
    assert day_plans[1].day_number == 2
    assert day_plans[1].stops[0].name == "Vatican Museums"


def test_parse_itinerary_markdown_ignores_non_day_sections():
    markdown = """
# Welcome
- Not a day stop

## Day 3: Coastal Day
- 08:00: Ferry to island | duration: 45 min
"""
    day_plans = parse_itinerary_markdown(markdown)
    assert len(day_plans) == 1
    assert day_plans[0].day_number == 3
    assert len(day_plans[0].stops) == 1

