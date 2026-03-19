"""
Core Google Places / Directions tool logic.

Pure functions that accept a googlemaps.Client — no MCP dependency,
making them easy to unit-test with a mocked client.
"""

import re
from typing import Any

import googlemaps

from mcp_servers.config import GoogleAPIQuotaError


def _check_quota_error(exc: Exception) -> None:
    """Re-raise as GoogleAPIQuotaError when the root cause is quota / billing."""
    msg = str(exc).upper()
    if "OVER_QUERY_LIMIT" in msg or "REQUEST_DENIED" in msg:
        raise GoogleAPIQuotaError(str(exc)) from exc


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


# ── Tool 1: search_places ────────────────────────────────────────────

def search_places(
    client: googlemaps.Client,
    query: str,
    location: str,
    radius: int = 5000,
    place_type: str = "tourist_attraction",
) -> list[dict[str, Any]]:
    """Geocode *location*, then run a Places Nearby Search.

    Returns the top 5 results with: name, rating, total_ratings,
    address, price_level, open_now, place_id, types.
    """
    try:
        geocode_results = client.geocode(location)
        if not geocode_results:
            return [{"error": f"Could not geocode location: {location}"}]

        coords = geocode_results[0]["geometry"]["location"]
        lat_lng = (coords["lat"], coords["lng"])

        response = client.places_nearby(
            location=lat_lng,
            radius=radius,
            keyword=query,
            type=place_type,
        )

        places = []
        for place in response.get("results", [])[:5]:
            opening = place.get("opening_hours", {})
            places.append({
                "name": place.get("name"),
                "rating": place.get("rating"),
                "total_ratings": place.get("user_ratings_total"),
                "address": place.get("vicinity"),
                "price_level": place.get("price_level"),
                "open_now": opening.get("open_now"),
                "place_id": place.get("place_id"),
                "types": place.get("types", []),
            })
        return places

    except googlemaps.exceptions.ApiError as exc:
        _check_quota_error(exc)
        return [{"error": str(exc)}]
    except googlemaps.exceptions.Timeout as exc:
        return [{"error": f"Google API timeout: {exc}"}]


# ── Tool 2: get_place_details ─────────────────────────────────────────

_DETAIL_FIELDS = [
    "name",
    "rating",
    "formatted_phone_number",
    "website",
    "opening_hours",
    "reviews",
    "price_level",
    "formatted_address",
    "geometry",
]


def get_place_details(
    client: googlemaps.Client,
    place_id: str,
) -> dict[str, Any]:
    """Fetch rich details for a single place.

    Returns: name, rating, phone, website, opening_hours,
    reviews (top 3), price_level, formatted_address, geometry.
    """
    try:
        resp = client.place(place_id, fields=_DETAIL_FIELDS)
        result = resp.get("result", {})

        reviews_raw = result.get("reviews", [])[:3]
        reviews = [
            {
                "author": r.get("author_name"),
                "rating": r.get("rating"),
                "text": r.get("text"),
                "time": r.get("relative_time_description"),
            }
            for r in reviews_raw
        ]

        hours = result.get("opening_hours", {})

        return {
            "name": result.get("name"),
            "rating": result.get("rating"),
            "phone": result.get("formatted_phone_number"),
            "website": result.get("website"),
            "opening_hours": hours.get("weekday_text", []),
            "reviews": reviews,
            "price_level": result.get("price_level"),
            "formatted_address": result.get("formatted_address"),
            "geometry": result.get("geometry", {}).get("location"),
        }

    except googlemaps.exceptions.ApiError as exc:
        _check_quota_error(exc)
        return {"error": str(exc)}
    except googlemaps.exceptions.Timeout as exc:
        return {"error": f"Google API timeout: {exc}"}


# ── Tool 3: get_directions ────────────────────────────────────────────

def get_directions(
    client: googlemaps.Client,
    origin: str,
    destination: str,
    mode: str = "transit",
) -> dict[str, Any]:
    """Get directions between two places.

    Returns: distance, duration, and the first 5 step-by-step
    instructions (HTML tags stripped).
    """
    try:
        results = client.directions(origin, destination, mode=mode)
        if not results:
            return {"error": "No route found between the specified locations."}

        leg = results[0]["legs"][0]
        steps = [
            {
                "instruction": _strip_html(s.get("html_instructions", "")),
                "distance": s.get("distance", {}).get("text"),
                "duration": s.get("duration", {}).get("text"),
            }
            for s in leg.get("steps", [])[:5]
        ]

        return {
            "distance": leg.get("distance", {}).get("text"),
            "duration": leg.get("duration", {}).get("text"),
            "steps": steps,
        }

    except googlemaps.exceptions.ApiError as exc:
        _check_quota_error(exc)
        return {"error": str(exc)}
    except googlemaps.exceptions.Timeout as exc:
        return {"error": f"Google API timeout: {exc}"}
