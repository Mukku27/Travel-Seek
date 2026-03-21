"""Tests for tools.weather_tool."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from tools.weather_tool import WeatherTools, _FORECAST_URL, _WEATHER_URL


@pytest.fixture
def weather_tools():
    return WeatherTools(api_key="test_api_key_123")


@pytest.fixture
def forecast_api_response():
    return {
        "city": {"name": "Paris", "country": "FR"},
        "list": [
            {
                "dt_txt": "2026-03-21 09:00:00",
                "main": {"temp": 8.5, "humidity": 72},
                "wind": {"speed": 3.2},
                "weather": [{"main": "Clouds"}],
            },
            {
                "dt_txt": "2026-03-21 15:00:00",
                "main": {"temp": 14.1, "humidity": 50},
                "wind": {"speed": 4.5},
                "weather": [{"main": "Clear"}],
            },
            {
                "dt_txt": "2026-03-22 09:00:00",
                "main": {"temp": 7.0, "humidity": 80},
                "wind": {"speed": 6.1},
                "weather": [{"main": "Rain"}],
            },
            {
                "dt_txt": "2026-03-22 15:00:00",
                "main": {"temp": 9.5, "humidity": 78},
                "wind": {"speed": 4.8},
                "weather": [{"main": "Drizzle"}],
            },
        ],
    }


@pytest.fixture
def current_weather_response():
    return {
        "dt": 1774072800,
        "name": "Paris",
        "sys": {"country": "FR"},
        "main": {"temp": 11.2, "feels_like": 10.1, "humidity": 68},
        "wind": {"speed": 3.8},
        "weather": [{"main": "Clouds", "description": "broken clouds"}],
    }


def _mock_response(status_code=200, json_data=None):
    mock = MagicMock(spec=requests.Response)
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


class TestToolkitRegistration:
    def test_toolkit_has_name(self, weather_tools):
        assert weather_tools.name == "weather_tools"

    def test_api_key_from_env(self):
        with patch.dict(os.environ, {"OPENWEATHERMAP_API_KEY": "env_key_456"}):
            tools = WeatherTools()
            assert tools.api_key == "env_key_456"

    def test_api_key_default_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("tools.weather_tool.load_dotenv"):
                tools = WeatherTools()
                assert tools.api_key == ""


class TestGetCurrentWeather:
    def test_success(self, weather_tools, current_weather_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, current_weather_response)

            result = json.loads(weather_tools.get_current_weather("Paris"))

            assert result["city"] == "Paris"
            assert result["country"] == "FR"
            assert result["current_temperature_celsius"] == 11.2
            assert result["condition"] == "Clouds"
            mock_get.assert_called_once_with(
                _WEATHER_URL,
                params={
                    "q": "Paris",
                    "appid": "test_api_key_123",
                    "units": "metric",
                },
                timeout=10,
            )

    def test_no_api_key(self):
        tools = WeatherTools(api_key="")
        result = json.loads(tools.get_current_weather("Paris"))
        assert "error" in result

    def test_timeout(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            result = json.loads(weather_tools.get_current_weather("Paris"))
            assert "timed out" in result["error"].lower()


class TestGetWeatherForecast:
    def test_successful_forecast(self, weather_tools, forecast_api_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, forecast_api_response)

            result = json.loads(weather_tools.get_weather_forecast("Paris", 2))

            assert result["city"] == "Paris"
            assert result["country"] == "FR"
            assert len(result["forecasts"]) == 2
            assert result["forecasts"][0]["temp_high_celsius"] == 14.1
            assert result["forecasts"][1]["is_outdoor_friendly"] is False

    def test_forecast_city_not_found(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(404)

            result = json.loads(weather_tools.get_weather_forecast("Missing", 3))
            assert "not found" in result["error"].lower()

    def test_forecast_invalid_api_key(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(401)

            result = json.loads(weather_tools.get_weather_forecast("Paris", 3))
            assert "invalid" in result["error"].lower()

    def test_forecast_timeout(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            result = json.loads(weather_tools.get_weather_forecast("Paris", 3))
            assert "timed out" in result["error"].lower()

    def test_forecast_passes_correct_params(self, weather_tools, forecast_api_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, forecast_api_response)

            weather_tools.get_weather_forecast("Tokyo,JP", 3)

            mock_get.assert_called_once_with(
                _FORECAST_URL,
                params={
                    "q": "Tokyo,JP",
                    "appid": "test_api_key_123",
                    "units": "metric",
                    "cnt": 24,
                },
                timeout=10,
            )


class TestGetTripWeatherGuidance:
    def test_exact_forecast_available(
        self,
        weather_tools,
        current_weather_response,
        forecast_api_response,
    ):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(200, current_weather_response),
                _mock_response(200, forecast_api_response),
            ]

            result = json.loads(
                weather_tools.get_trip_weather_guidance(
                    "Paris",
                    "2026-03-21",
                    "2026-03-22",
                ),
            )

            assert result["exact_forecast_available"] is True
            assert len(result["forecasts"]) == 2
            assert result["missing_dates"] == []
            assert result["packing_guidance"]

    def test_partial_forecast_window_returns_limitation_note(
        self,
        weather_tools,
        current_weather_response,
        forecast_api_response,
    ):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(200, current_weather_response),
                _mock_response(200, forecast_api_response),
            ]

            result = json.loads(
                weather_tools.get_trip_weather_guidance(
                    "Paris",
                    "2026-03-22",
                    "2026-03-24",
                ),
            )

            assert result["exact_forecast_available"] is False
            assert result["missing_dates"] == ["2026-03-23", "2026-03-24"]
            assert "do not infer weather" in result["note"].lower()
            assert "recommended_recheck_date" in result
            assert "Layered clothing for variable conditions" in result["packing_guidance"]

    def test_invalid_date_format(self, weather_tools):
        result = json.loads(
            weather_tools.get_trip_weather_guidance("Paris", "03/21/2026", "2026-03-22"),
        )
        assert "iso format" in result["error"].lower()

    def test_end_before_start(self, weather_tools):
        result = json.loads(
            weather_tools.get_trip_weather_guidance("Paris", "2026-03-22", "2026-03-21"),
        )
        assert "on or after" in result["error"].lower()


class TestHistoricalWeatherCompatibility:
    def test_returns_honest_limitation_message(self, weather_tools, current_weather_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, current_weather_response)

            result = json.loads(weather_tools.get_historical_weather("Paris", 7))

            assert result["supported"] is False
            assert "not available" in result["note"].lower()
            assert result["requested_month_name"] == "July"

    def test_invalid_month(self, weather_tools):
        result = json.loads(weather_tools.get_historical_weather("Paris", 13))
        assert "invalid month" in result["error"].lower()


class TestAggregateForecast:
    def test_aggregates_by_date(self):
        data = {
            "list": [
                {
                    "dt_txt": "2026-04-01 09:00:00",
                    "main": {"temp": 15, "humidity": 60},
                    "wind": {"speed": 3},
                    "weather": [{"main": "Clear"}],
                },
                {
                    "dt_txt": "2026-04-01 15:00:00",
                    "main": {"temp": 20, "humidity": 50},
                    "wind": {"speed": 5},
                    "weather": [{"main": "Clear"}],
                },
            ],
        }

        result = WeatherTools._aggregate_forecast(data, 1)

        assert len(result) == 1
        assert result[0]["date"] == "2026-04-01"
        assert result[0]["temp_high_celsius"] == 20
        assert result[0]["temp_low_celsius"] == 15
        assert result[0]["condition"] == "Clear"
        assert result[0]["is_outdoor_friendly"] is True
