"""Tests for mcp_servers.places_tools — all Google API calls are mocked."""

from unittest.mock import MagicMock, patch

import pytest

import googlemaps.exceptions
from mcp_servers.config import GoogleAPIQuotaError
from mcp_servers.places_tools import (
    search_places,
    get_place_details,
    get_directions,
    _strip_html,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_client():
    return MagicMock()


# ── _strip_html ───────────────────────────────────────────────────────

def test_strip_html_basic():
    assert _strip_html("<b>Hello</b> <i>world</i>") == "Hello world"


def test_strip_html_no_tags():
    assert _strip_html("plain text") == "plain text"


# ── search_places ─────────────────────────────────────────────────────

def test_search_places_returns_top_5(mock_client):
    mock_client.geocode.return_value = [
        {"geometry": {"location": {"lat": 48.8566, "lng": 2.3522}}}
    ]
    mock_client.places_nearby.return_value = {
        "results": [
            {
                "name": f"Place {i}",
                "rating": 4.0 + i * 0.1,
                "user_ratings_total": 100 * i,
                "vicinity": f"Address {i}",
                "price_level": 2,
                "opening_hours": {"open_now": True},
                "place_id": f"place_id_{i}",
                "types": ["tourist_attraction"],
            }
            for i in range(8)
        ]
    }

    results = search_places(mock_client, "museums", "Paris, France")

    assert len(results) == 5
    assert results[0]["name"] == "Place 0"
    assert results[4]["name"] == "Place 4"
    for r in results:
        assert "place_id" in r
        assert "rating" in r
        assert "open_now" in r


def test_search_places_empty_results(mock_client):
    mock_client.geocode.return_value = [
        {"geometry": {"location": {"lat": 0, "lng": 0}}}
    ]
    mock_client.places_nearby.return_value = {"results": []}

    results = search_places(mock_client, "xyz", "Nowhere")
    assert results == []


def test_search_places_geocode_failure(mock_client):
    mock_client.geocode.return_value = []

    results = search_places(mock_client, "museums", "Unknown Place")
    assert len(results) == 1
    assert "error" in results[0]
    assert "Could not geocode" in results[0]["error"]


def test_search_places_quota_error(mock_client):
    mock_client.geocode.side_effect = googlemaps.exceptions.ApiError(
        "OVER_QUERY_LIMIT"
    )

    with pytest.raises(GoogleAPIQuotaError):
        search_places(mock_client, "test", "Paris")


def test_search_places_request_denied(mock_client):
    mock_client.geocode.side_effect = googlemaps.exceptions.ApiError(
        "REQUEST_DENIED"
    )

    with pytest.raises(GoogleAPIQuotaError):
        search_places(mock_client, "test", "Paris")


def test_search_places_generic_api_error(mock_client):
    mock_client.geocode.side_effect = googlemaps.exceptions.ApiError(
        "INVALID_REQUEST"
    )

    results = search_places(mock_client, "test", "Paris")
    assert len(results) == 1
    assert "error" in results[0]


def test_search_places_timeout(mock_client):
    mock_client.geocode.side_effect = googlemaps.exceptions.Timeout()

    results = search_places(mock_client, "test", "Paris")
    assert len(results) == 1
    assert "timeout" in results[0]["error"].lower()


def test_search_places_custom_radius_and_type(mock_client):
    mock_client.geocode.return_value = [
        {"geometry": {"location": {"lat": 35.6762, "lng": 139.6503}}}
    ]
    mock_client.places_nearby.return_value = {"results": []}

    search_places(
        mock_client, "ramen", "Tokyo", radius=10000, place_type="restaurant"
    )

    mock_client.places_nearby.assert_called_once_with(
        location=(35.6762, 139.6503),
        radius=10000,
        keyword="ramen",
        type="restaurant",
    )


# ── get_place_details ─────────────────────────────────────────────────

def test_get_place_details_success(mock_client):
    mock_client.place.return_value = {
        "result": {
            "name": "Eiffel Tower",
            "rating": 4.7,
            "formatted_phone_number": "+33 1 23 45 67 89",
            "website": "https://www.toureiffel.paris",
            "opening_hours": {
                "weekday_text": ["Monday: 9:00 AM – 11:00 PM"],
            },
            "reviews": [
                {
                    "author_name": "Alice",
                    "rating": 5,
                    "text": "Amazing!",
                    "relative_time_description": "a month ago",
                },
                {
                    "author_name": "Bob",
                    "rating": 4,
                    "text": "Great views",
                    "relative_time_description": "2 months ago",
                },
                {
                    "author_name": "Charlie",
                    "rating": 5,
                    "text": "Must visit",
                    "relative_time_description": "3 months ago",
                },
                {
                    "author_name": "Dave",
                    "rating": 3,
                    "text": "Crowded",
                    "relative_time_description": "4 months ago",
                },
            ],
            "price_level": 2,
            "formatted_address": "Champ de Mars, 5 Av. Anatole France",
            "geometry": {"location": {"lat": 48.8584, "lng": 2.2945}},
        }
    }

    result = get_place_details(mock_client, "ChIJLU7jZClu5kcR4PcOOO6p3I0")

    assert result["name"] == "Eiffel Tower"
    assert result["rating"] == 4.7
    assert result["phone"] == "+33 1 23 45 67 89"
    assert result["website"] == "https://www.toureiffel.paris"
    assert len(result["reviews"]) == 3  # capped at 3
    assert result["reviews"][0]["author"] == "Alice"
    assert result["geometry"]["lat"] == 48.8584


def test_get_place_details_minimal_data(mock_client):
    mock_client.place.return_value = {"result": {"name": "Simple Place"}}

    result = get_place_details(mock_client, "some_id")

    assert result["name"] == "Simple Place"
    assert result["rating"] is None
    assert result["reviews"] == []
    assert result["opening_hours"] == []


def test_get_place_details_quota_error(mock_client):
    mock_client.place.side_effect = googlemaps.exceptions.ApiError(
        "OVER_QUERY_LIMIT"
    )

    with pytest.raises(GoogleAPIQuotaError):
        get_place_details(mock_client, "id")


def test_get_place_details_timeout(mock_client):
    mock_client.place.side_effect = googlemaps.exceptions.Timeout()

    result = get_place_details(mock_client, "id")
    assert "error" in result
    assert "timeout" in result["error"].lower()


# ── get_directions ────────────────────────────────────────────────────

def test_get_directions_success(mock_client):
    mock_client.directions.return_value = [
        {
            "legs": [
                {
                    "distance": {"text": "5.2 km"},
                    "duration": {"text": "18 mins"},
                    "steps": [
                        {
                            "html_instructions": "Head <b>north</b> on Rue de Rivoli",
                            "distance": {"text": "1.0 km"},
                            "duration": {"text": "5 mins"},
                        },
                        {
                            "html_instructions": "Turn <b>left</b> onto Bd Saint-Michel",
                            "distance": {"text": "2.0 km"},
                            "duration": {"text": "7 mins"},
                        },
                        {
                            "html_instructions": "Continue onto <b>Av. de l'Observatoire</b>",
                            "distance": {"text": "0.5 km"},
                            "duration": {"text": "2 mins"},
                        },
                    ],
                }
            ]
        }
    ]

    result = get_directions(mock_client, "Louvre", "Pantheon")

    assert result["distance"] == "5.2 km"
    assert result["duration"] == "18 mins"
    assert len(result["steps"]) == 3
    assert "<b>" not in result["steps"][0]["instruction"]
    assert "north" in result["steps"][0]["instruction"]


def test_get_directions_no_route(mock_client):
    mock_client.directions.return_value = []

    result = get_directions(mock_client, "A", "B")
    assert "error" in result
    assert "No route found" in result["error"]


def test_get_directions_limits_to_5_steps(mock_client):
    mock_client.directions.return_value = [
        {
            "legs": [
                {
                    "distance": {"text": "10 km"},
                    "duration": {"text": "30 mins"},
                    "steps": [
                        {
                            "html_instructions": f"Step {i}",
                            "distance": {"text": "1 km"},
                            "duration": {"text": "3 mins"},
                        }
                        for i in range(10)
                    ],
                }
            ]
        }
    ]

    result = get_directions(mock_client, "A", "B")
    assert len(result["steps"]) == 5


def test_get_directions_modes(mock_client):
    mock_client.directions.return_value = [
        {
            "legs": [
                {
                    "distance": {"text": "1 km"},
                    "duration": {"text": "5 mins"},
                    "steps": [],
                }
            ]
        }
    ]

    for mode in ("driving", "walking", "bicycling", "transit"):
        get_directions(mock_client, "A", "B", mode=mode)
        mock_client.directions.assert_called_with("A", "B", mode=mode)


def test_get_directions_quota_error(mock_client):
    mock_client.directions.side_effect = googlemaps.exceptions.ApiError(
        "REQUEST_DENIED"
    )

    with pytest.raises(GoogleAPIQuotaError):
        get_directions(mock_client, "A", "B")


def test_get_directions_timeout(mock_client):
    mock_client.directions.side_effect = googlemaps.exceptions.Timeout()

    result = get_directions(mock_client, "A", "B")
    assert "error" in result
