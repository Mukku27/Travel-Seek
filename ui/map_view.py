"""Map rendering helpers for itinerary visualization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import folium
import requests

from ui.itinerary_parser import DayPlan, Stop

DAY_COLORS = [
    "#d73027",
    "#4575b4",
    "#1a9850",
    "#984ea3",
    "#ff7f00",
    "#66c2a5",
]


@dataclass
class MappedStop:
    """A stop with guaranteed map coordinates."""

    day_number: int
    stop: Stop
    latitude: float
    longitude: float


def day_color(day_number: int) -> str:
    """Return a deterministic color for a given day index."""
    if day_number <= 0:
        return DAY_COLORS[0]
    return DAY_COLORS[(day_number - 1) % len(DAY_COLORS)]


def geocode_location(name: str, destination: str) -> Optional[tuple[float, float]]:
    """Resolve a stop name into coordinates using OpenStreetMap Nominatim."""
    query = f"{name}, {destination}" if destination else name
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1},
        timeout=8,
        headers={"User-Agent": "travel-seek-itinerary-map/1.0"},
    )
    response.raise_for_status()
    payload = response.json()
    if not payload:
        return None
    top_hit = payload[0]
    return float(top_hit["lat"]), float(top_hit["lon"])


def collect_mapped_stops(
    day_plans: list[DayPlan],
    destination: str,
    geocode_cache: dict[str, Optional[tuple[float, float]]],
) -> list[MappedStop]:
    """Collect all stops with coordinates, geocoding missing entries lazily."""
    mapped_stops: list[MappedStop] = []
    for day_plan in day_plans:
        for stop in day_plan.stops:
            latitude = stop.latitude
            longitude = stop.longitude

            if latitude is None or longitude is None:
                cache_key = f"{destination}::{stop.name}".strip()
                if cache_key not in geocode_cache:
                    try:
                        geocode_cache[cache_key] = geocode_location(stop.name, destination)
                    except Exception:
                        geocode_cache[cache_key] = None
                cached = geocode_cache.get(cache_key)
                if cached:
                    latitude, longitude = cached

            if latitude is None or longitude is None:
                continue

            mapped_stops.append(
                MappedStop(
                    day_number=day_plan.day_number,
                    stop=stop,
                    latitude=latitude,
                    longitude=longitude,
                )
            )
    return mapped_stops


def build_itinerary_map(
    day_plans: list[DayPlan],
    destination: str,
    geocode_cache: dict[str, Optional[tuple[float, float]]],
) -> Optional[folium.Map]:
    """Build a Folium map with day-colored markers and route polylines."""
    mapped_stops = collect_mapped_stops(day_plans, destination, geocode_cache)
    if not mapped_stops:
        return None

    center_lat = sum(stop.latitude for stop in mapped_stops) / len(mapped_stops)
    center_lon = sum(stop.longitude for stop in mapped_stops) / len(mapped_stops)
    itinerary_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="CartoDB Positron",
        control_scale=True,
    )

    bounds: list[list[float]] = []
    by_day: dict[int, list[MappedStop]] = {}
    for mapped in mapped_stops:
        by_day.setdefault(mapped.day_number, []).append(mapped)
        color = day_color(mapped.day_number)
        popup_html = (
            f"<b>{mapped.stop.name}</b><br>"
            f"Time: {mapped.stop.time}<br>"
            f"Rating: {mapped.stop.rating}"
        )
        folium.CircleMarker(
            location=[mapped.latitude, mapped.longitude],
            radius=7,
            color=color,
            fill=True,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Day {mapped.day_number}: {mapped.stop.name}",
        ).add_to(itinerary_map)
        bounds.append([mapped.latitude, mapped.longitude])

    for day_number, stops in by_day.items():
        if len(stops) < 2:
            continue
        folium.PolyLine(
            locations=[[item.latitude, item.longitude] for item in stops],
            color=day_color(day_number),
            weight=4,
            opacity=0.75,
            tooltip=f"Day {day_number} route",
        ).add_to(itinerary_map)

    itinerary_map.fit_bounds(bounds)
    return itinerary_map

