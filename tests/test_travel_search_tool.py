"""Tests for tools.travel_search_tool."""

import json
from unittest.mock import MagicMock, patch

import requests

from tools.travel_search_tool import TravelSearchTools, _SERPAPI_SEARCH_URL


def _mock_response(status_code=200, payload=None):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.json.return_value = payload or {}
    response.raise_for_status.return_value = None
    return response


def test_missing_api_key_returns_error():
    tools = TravelSearchTools(api_key="")
    result = json.loads(
        tools.search_flights(
            origin="SFO",
            destination="JFK",
            departure_date="2026-04-10",
            return_date="2026-04-15",
        ),
    )
    assert "SERPI_API_KEY" in result["error"]


def test_search_flights_normalizes_and_sorts_prices():
    tools = TravelSearchTools(api_key="test_key")
    payload = {
        "search_metadata": {"google_flights_url": "https://www.google.com/travel/flights"},
        "best_flights": [
            {
                "price": "$1,240",
                "flights": [
                    {
                        "airline": "Delta",
                        "departure_airport": {"name": "SFO", "time": "8:30 AM"},
                        "arrival_airport": {"name": "JFK", "time": "4:45 PM"},
                    },
                ],
                "total_duration": "8 hr 15 min",
            },
        ],
        "other_flights": [
            {
                "price": "$999",
                "flights": [
                    {
                        "airline": "United",
                        "departure_airport": {"name": "SFO", "time": "7:00 AM"},
                        "arrival_airport": {"name": "JFK", "time": "3:20 PM"},
                    },
                ],
                "total_duration": "8 hr 20 min",
            },
        ],
    }

    with patch("tools.travel_search_tool.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload=payload)

        result = json.loads(
            tools.search_flights(
                origin="SFO",
                destination="JFK",
                departure_date="2026-04-10",
                return_date="2026-04-15",
                adults=2,
                currency="usd",
            ),
        )

    assert len(result["flight_options"]) == 2
    assert result["flight_options"][0]["price_value"] == 999.0
    assert result["flight_options"][0]["booking_url"] == "https://www.google.com/travel/flights"
    mock_get.assert_called_once_with(
        _SERPAPI_SEARCH_URL,
        params={
            "engine": "google_flights",
            "departure_id": "SFO",
            "arrival_id": "JFK",
            "outbound_date": "2026-04-10",
            "adults": 2,
            "currency": "USD",
            "travel_class": "economy",
            "hl": "en",
            "return_date": "2026-04-15",
            "api_key": "test_key",
        },
        timeout=15,
    )


def test_search_hotels_normalizes_and_sorts_prices():
    tools = TravelSearchTools(api_key="test_key")
    payload = {
        "search_metadata": {"google_hotels_url": "https://www.google.com/travel/hotels"},
        "properties": [
            {
                "name": "Central Suites",
                "overall_rating": 4.7,
                "reviews": 421,
                "rate_per_night": {"lowest": "$210"},
                "total_rate": {"lowest": "$840"},
                "link": "https://booking.example/hotel-1",
            },
            {
                "name": "City Budget Inn",
                "overall_rating": 4.2,
                "reviews": 201,
                "rate_per_night": {"lowest": "$120"},
                "total_rate": {"lowest": "$480"},
                "link": "https://booking.example/hotel-2",
            },
        ],
    }

    with patch("tools.travel_search_tool.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload=payload)
        result = json.loads(
            tools.search_hotels(
                destination="New York",
                check_in_date="2026-04-10",
                check_out_date="2026-04-14",
                adults=2,
            ),
        )

    assert len(result["hotel_options"]) == 2
    assert result["hotel_options"][0]["name"] == "City Budget Inn"
    assert result["hotel_options"][0]["nightly_rate_value"] == 120.0
    assert result["hotel_options"][0]["booking_url"] == "https://booking.example/hotel-2"


def test_get_trip_price_estimates_returns_tiered_costs_and_links():
    tools = TravelSearchTools(api_key="test_key")
    flight_payload = {
        "search_metadata": {"google_flights_url": "https://www.google.com/travel/flights"},
        "best_flights": [
            {
                "price": "$700",
                "flights": [
                    {
                        "airline": "United",
                        "departure_airport": {"name": "SFO", "time": "9:00 AM"},
                        "arrival_airport": {"name": "JFK", "time": "5:30 PM"},
                    },
                ],
            },
            {
                "price": "$900",
                "flights": [
                    {
                        "airline": "Delta",
                        "departure_airport": {"name": "SFO", "time": "11:00 AM"},
                        "arrival_airport": {"name": "JFK", "time": "7:25 PM"},
                    },
                ],
            },
        ],
    }
    hotel_payload = {
        "search_metadata": {"google_hotels_url": "https://www.google.com/travel/hotels"},
        "properties": [
            {"name": "A", "rate_per_night": {"lowest": "$120"}, "link": "https://hotel-a"},
            {"name": "B", "rate_per_night": {"lowest": "$180"}, "link": "https://hotel-b"},
            {"name": "C", "rate_per_night": {"lowest": "$260"}, "link": "https://hotel-c"},
        ],
    }

    with patch("tools.travel_search_tool.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(payload=flight_payload),
            _mock_response(payload=hotel_payload),
        ]
        result = json.loads(
            tools.get_trip_price_estimates(
                origin="SFO",
                destination="JFK",
                departure_date="2026-04-10",
                return_date="2026-04-14",
                adults=2,
                currency="usd",
            ),
        )

    assert result["nights"] == 4
    assert result["tier_estimates"]["budget"]["flight_total_for_travelers"] == 1400.0
    assert result["tier_estimates"]["budget"]["hotel_total_for_stay"] == 480.0
    assert result["tier_estimates"]["budget"]["estimated_total"] == 1880.0
    assert result["tier_estimates"]["luxury"]["flight_per_person"] == 900.0
    assert "https://www.google.com/travel/flights" in result["booking_links"]["flights"]
    assert "https://hotel-a" in result["booking_links"]["hotels"]


def test_get_trip_price_estimates_validates_date_window():
    tools = TravelSearchTools(api_key="test_key")
    result = json.loads(
        tools.get_trip_price_estimates(
            origin="SFO",
            destination="JFK",
            departure_date="04-10-2026",
            return_date="2026-04-14",
        ),
    )
    assert "ISO format" in result["error"]


def test_search_request_timeout_returns_error():
    tools = TravelSearchTools(api_key="test_key")
    with patch("tools.travel_search_tool.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout()
        result = json.loads(
            tools.search_hotels(
                destination="New York",
                check_in_date="2026-04-10",
                check_out_date="2026-04-14",
            ),
        )
    assert "timed out" in result["error"].lower()
