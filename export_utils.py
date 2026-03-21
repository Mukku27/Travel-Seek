"""Export helpers for itinerary markdown, PDF, and calendar files."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta




def extract_itinerary_structure(markdown_text: str, destination: str = "") -> list[dict]:
    if not markdown_text:
        return []
    day_sections = []
    current_day = None
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        day_match = re.match(r"^(?:#+\s*)?(Day\s+\d+[:\-]?.*)$", line, flags=re.IGNORECASE)
        if day_match:
            current_day = {"title": day_match.group(1).strip(), "stops": []}
            day_sections.append(current_day)
            continue
        if current_day is None:
            continue
        if line.startswith(("-", "*")) or re.match(r"^\d+[.)]\s+", line):
            current_day["stops"].append(_parse_stop_line(line, destination))
    return [day for day in day_sections if day["stops"]]


def _parse_stop_line(line: str, destination: str) -> dict:
    cleaned = re.sub(r"^[-*]\s+|^\d+[.)]\s+", "", line).strip()
    cleaned = re.sub(r"[*_`]+", "", cleaned)
    time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s?(?:AM|PM|am|pm)?)\b", cleaned)
    rating_match = re.search(r"(?:rating|⭐)[:\s]*([0-5](?:\.\d)?)", cleaned, flags=re.IGNORECASE)
    cost_match = re.search(r"(?:\$|USD\s?)\d[\d,.]*", cleaned)
    duration_match = re.search(r"(\d+\s?(?:min|mins|minutes|hr|hrs|hours))", cleaned, flags=re.IGNORECASE)
    distance_match = re.search(r"(\d+(?:\.\d+)?\s?(?:km|mi|miles))", cleaned, flags=re.IGNORECASE)
    title = re.split(r"[—|-]\s+|:\s+", cleaned, maxsplit=1)[0].strip()
    if time_match:
        title = title.replace(time_match.group(1), "").strip(" ,-|")
    return {
        "name": title or cleaned[:60],
        "time": time_match.group(1) if time_match else "Flexible",
        "rating": rating_match.group(1) if rating_match else None,
        "cost_estimate": cost_match.group(0) if cost_match else None,
        "duration": duration_match.group(1) if duration_match else None,
        "distance_to_next": distance_match.group(1) if distance_match else None,
        "details": cleaned,
        "query": ", ".join(part for part in [title, destination] if part),
    }


def build_markdown_export(travel_plan: str) -> str:
    return travel_plan or ""


def build_pdf_export(
    destination: str,
    travel_plan: str,
    start_date: date,
    end_date: date,
    budget: str,
    travel_style: list[str],
) -> bytes:
    itinerary_days = extract_itinerary_structure(travel_plan, destination)
    lines = [
        f"Travel-Seek Itinerary: {destination or 'Your Trip'}",
        f"Dates: {start_date.isoformat()} to {end_date.isoformat()}",
        f"Budget tier: {budget}",
        f"Travel style: {', '.join(travel_style) or 'Flexible'}",
        "",
        "Day-by-Day Itinerary",
    ]
    for day in itinerary_days:
        lines.append(day["title"])
        for stop in day["stops"]:
            extras = [value for value in [stop.get('duration'), stop.get('cost_estimate'), stop.get('rating')] if value]
            suffix = f" ({', '.join(extras)})" if extras else ""
            lines.append(f"- {stop['time']} | {stop['name']}{suffix}")
            lines.append(f"  {stop['details']}")
    lines.extend([
        "",
        "Budget Summary",
        f"Selected tier: {budget}",
        f"Trip length: {(end_date - start_date).days + 1} days",
        "Use the generated budget section for detailed cost ranges.",
        "",
        "Cultural Tips",
        _extract_section(travel_plan, ["Cultural", "Local", "Etiquette", "Tips"]) or "Refer to the Local Expert section in the markdown export for destination-specific advice.",
        "",
        "Emergency Contacts",
        _build_emergency_contacts(destination),
    ])
    return _build_simple_pdf(lines)


def build_calendar_export(destination: str, travel_plan: str, start_date: date) -> bytes:
    itinerary_days = extract_itinerary_structure(travel_plan, destination)
    rows = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Travel Seek//Itinerary Export//EN",
        "CALSCALE:GREGORIAN",
    ]
    for day_index, day in enumerate(itinerary_days):
        current_date = start_date + timedelta(days=day_index)
        cursor = datetime.combine(current_date, datetime.min.time()).replace(hour=9)
        for stop in day["stops"]:
            start_dt = _coerce_stop_datetime(current_date, stop.get("time"), cursor)
            end_dt = start_dt + _duration_to_delta(stop.get("duration"))
            cursor = end_dt + timedelta(minutes=30)
            uid = f"{current_date.isoformat()}-{slugify(stop['name'])}@travelseek"
            rows.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{escape_ics(stop['name'])}",
                f"LOCATION:{escape_ics(stop.get('query') or destination)}",
                f"DESCRIPTION:{escape_ics(stop.get('details') or f'Itinerary stop for {destination}')}",
                "END:VEVENT",
            ])
    rows.append("END:VCALENDAR")
    return ("\r\n".join(rows) + "\r\n").encode("utf-8")


def escape_ics(value: str) -> str:
    return (value or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "event"


def _coerce_stop_datetime(current_date: date, raw_time: str | None, fallback: datetime) -> datetime:
    if not raw_time or raw_time == "Flexible":
        return fallback
    for fmt in ("%I:%M %p", "%I %p"):
        try:
            parsed = datetime.strptime(raw_time.upper().replace('.', ''), fmt)
            return datetime.combine(current_date, parsed.time())
        except ValueError:
            continue
    return fallback


def _duration_to_delta(raw_duration: str | None) -> timedelta:
    if not raw_duration:
        return timedelta(hours=2)
    match = re.search(r"(\d+)\s*(min|mins|minutes|hr|hrs|hours)", raw_duration, flags=re.IGNORECASE)
    if not match:
        return timedelta(hours=2)
    amount = int(match.group(1))
    unit = match.group(2).lower()
    return timedelta(hours=amount) if unit.startswith("h") else timedelta(minutes=amount)


def _extract_section(text: str, keywords: list[str]) -> str:
    for paragraph in text.split("\n\n"):
        if any(keyword.lower() in paragraph.lower() for keyword in keywords):
            return paragraph.strip()
    return ""


def _build_emergency_contacts(destination: str) -> str:
    return (
        f"Destination: {destination or 'Unknown'}\n"
        "Verify local police, ambulance, and fire numbers before departure.\n"
        "Keep embassy, travel insurance, airline, and hotel contacts accessible.\n"
        "Share your itinerary and passport copies with a trusted contact."
    )


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf(lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 12 Tf", "50 780 Td", "14 TL"]
    first = True
    for line in lines:
        if not first:
            content_lines.append("T*")
        content_lines.append(f"({_pdf_escape(line)}) Tj")
        first = False
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("ascii") + stream + b"\nendstream endobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("ascii")
    )
    return bytes(pdf)
