"""Tests for the FastMCP server registration and tool schemas."""

import json
from unittest.mock import patch, MagicMock

import pytest

from mcp_servers.places_server import mcp, search_places, get_place_details, get_directions


def test_server_has_name():
    assert mcp.name == "travel-seek-places"


def test_search_places_returns_json():
    mock_client = MagicMock()
    mock_client.geocode.return_value = [
        {"geometry": {"location": {"lat": 48.85, "lng": 2.35}}}
    ]
    mock_client.places_nearby.return_value = {
        "results": [
            {
                "name": "Test Place",
                "rating": 4.5,
                "user_ratings_total": 200,
                "vicinity": "123 Rue",
                "price_level": 2,
                "opening_hours": {"open_now": True},
                "place_id": "abc123",
                "types": ["museum"],
            }
        ]
    }

    with patch("mcp_servers.places_server.get_gmaps_client", return_value=mock_client):
        result = search_places("museums", "Paris", radius=5000, type="museum")

    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "Test Place"


def test_get_place_details_returns_json():
    mock_client = MagicMock()
    mock_client.place.return_value = {
        "result": {
            "name": "Louvre",
            "rating": 4.8,
            "formatted_address": "Rue de Rivoli",
        }
    }

    with patch("mcp_servers.places_server.get_gmaps_client", return_value=mock_client):
        result = get_place_details("place_id_123")

    parsed = json.loads(result)
    assert parsed["name"] == "Louvre"


def test_get_directions_returns_json():
    mock_client = MagicMock()
    mock_client.directions.return_value = [
        {
            "legs": [
                {
                    "distance": {"text": "3 km"},
                    "duration": {"text": "10 mins"},
                    "steps": [
                        {
                            "html_instructions": "Go <b>straight</b>",
                            "distance": {"text": "3 km"},
                            "duration": {"text": "10 mins"},
                        }
                    ],
                }
            ]
        }
    ]

    with patch("mcp_servers.places_server.get_gmaps_client", return_value=mock_client):
        result = get_directions("A", "B", mode="walking")

    parsed = json.loads(result)
    assert parsed["distance"] == "3 km"
    assert parsed["duration"] == "10 mins"
    assert len(parsed["steps"]) == 1


def test_search_places_propagates_quota_error():
    mock_client = MagicMock()
    import googlemaps.exceptions
    mock_client.geocode.side_effect = googlemaps.exceptions.ApiError(
        "OVER_QUERY_LIMIT"
    )

    with patch("mcp_servers.places_server.get_gmaps_client", return_value=mock_client):
        from mcp_servers.config import GoogleAPIQuotaError
        with pytest.raises(GoogleAPIQuotaError):
            search_places("test", "Paris")
