"""Helpers for transforming markdown travel plans into structured itinerary data."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Optional

DAY_HEADING_RE = re.compile(
    r"^\s{0,3}(?:#+\s*)?(?:\*\*)?\s*Day\s*(?P<day>\d+)\b[:\- ]*(?P<title>.*?)(?:\*\*)?\s*$",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(?P<body>.+)")
TIME_PREFIX_RE = re.compile(
    r"^(?P<time>\d{1,2}(?::\d{2})?\s*(?:AM|PM)?(?:\s*(?:-|–|to)\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)?)\s*[:\-]\s*(?P<body>.+)$",
    re.IGNORECASE,
)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
COORD_PAIR_RE = re.compile(r"\((?P<lat>-?\d{1,2}\.\d+)\s*,\s*(?P<lon>-?\d{1,3}\.\d+)\)")
COORD_LABELED_RE = re.compile(
    r"lat(?:itude)?\s*[:=]\s*(?P<lat>-?\d{1,2}\.\d+).*?(?:lon|lng|longitude)\s*[:=]\s*(?P<lon>-?\d{1,3}\.\d+)",
    re.IGNORECASE,
)
RATING_RE = re.compile(
    r"(?:rating\s*[:=]?\s*(?P<named>\d(?:\.\d+)?))|(?P<slash>\d(?:\.\d+)?)\s*/\s*5",
    re.IGNORECASE,
)
DURATION_RE = re.compile(
    r"duration\s*[:=]?\s*(?P<duration>\d+(?:\.\d+)?\s*(?:hours|hour|hrs|hr|h|minutes|mins|min))",
    re.IGNORECASE,
)
COST_RE = re.compile(
    r"(?:cost|price|estimate)\s*[:=]?\s*(?P<cost>[^|;,)\]]+)",
    re.IGNORECASE,
)
DISTANCE_RE = re.compile(
    r"distance(?:\s+to\s+next)?\s*[:=]?\s*(?P<distance>[^|;,)\]]+)",
    re.IGNORECASE,
)


@dataclass
class Stop:
    """A single itinerary stop shown in day cards and map popups."""

    name: str
    time: str = "Flexible"
    duration: str = "N/A"
    rating: str = "N/A"
    cost_estimate: str = "N/A"
    distance_to_next: str = "N/A"
    notes: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class DayPlan:
    """A normalized day section from the markdown itinerary."""

    day_number: int
    title: str = ""
    stops: list[Stop] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.title:
            return f"Day {self.day_number}: {self.title}"
        return f"Day {self.day_number}"


def _strip_markdown_links(text: str) -> str:
    return MARKDOWN_LINK_RE.sub(r"\1", text)


def _extract_coordinates(text: str) -> tuple[Optional[float], Optional[float]]:
    labeled_match = COORD_LABELED_RE.search(text)
    if labeled_match:
        return float(labeled_match.group("lat")), float(labeled_match.group("lon"))

    pair_match = COORD_PAIR_RE.search(text)
    if pair_match:
        return float(pair_match.group("lat")), float(pair_match.group("lon"))

    return None, None


def _extract_field(text: str, regex: re.Pattern[str], group: str) -> Optional[str]:
    match = regex.search(text)
    if not match:
        return None
    raw_value = match.group(group)
    return raw_value.strip() if raw_value else None


def _extract_rating(text: str) -> Optional[str]:
    match = RATING_RE.search(text)
    if not match:
        return None
    value = match.group("named") or match.group("slash")
    return value.strip() if value else None


def _extract_name(body: str) -> str:
    parts = re.split(r"\s+\|\s+|(?=\bduration\b)|(?=\brating\b)|(?=\bcost\b)|(?=\bprice\b)|(?=\bdistance\b)", body, maxsplit=1, flags=re.IGNORECASE)
    base = parts[0]
    base = re.sub(r"\([^)]*\)", "", base)
    base = base.strip(" -:")
    return base.strip() or "Planned Stop"


def parse_stop_line(line: str) -> Optional[Stop]:
    """Parse a single markdown bullet line into a Stop object."""
    bullet_match = BULLET_RE.match(line)
    if not bullet_match:
        return None

    body = _strip_markdown_links(bullet_match.group("body")).strip()
    time_value = "Flexible"
    time_match = TIME_PREFIX_RE.match(body)
    if time_match:
        time_value = time_match.group("time").strip()
        body = time_match.group("body").strip()

    latitude, longitude = _extract_coordinates(body)
    rating = _extract_rating(body) or "N/A"
    duration = _extract_field(body, DURATION_RE, "duration") or "N/A"
    cost = _extract_field(body, COST_RE, "cost") or "N/A"
    distance = _extract_field(body, DISTANCE_RE, "distance") or "N/A"
    name = _extract_name(body)

    return Stop(
        name=name,
        time=time_value,
        duration=duration,
        rating=rating,
        cost_estimate=cost,
        distance_to_next=distance,
        notes=body,
        latitude=latitude,
        longitude=longitude,
    )


def parse_itinerary_markdown(plan_markdown: str) -> list[DayPlan]:
    """Extract day sections and stops from an LLM-generated markdown itinerary."""
    if not plan_markdown:
        return []

    day_plans: list[DayPlan] = []
    current_day: Optional[DayPlan] = None

    for raw_line in plan_markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading_match = DAY_HEADING_RE.match(line)
        if heading_match:
            current_day = DayPlan(
                day_number=int(heading_match.group("day")),
                title=heading_match.group("title").strip(" :-"),
            )
            day_plans.append(current_day)
            continue

        if current_day is None:
            continue

        stop = parse_stop_line(line)
        if stop:
            current_day.stops.append(stop)

    return sorted(day_plans, key=lambda item: item.day_number)
