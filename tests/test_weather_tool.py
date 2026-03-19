"""Tests for tools.weather_tool — all OpenWeatherMap API calls are mocked."""

import json
import os
from unittest.mock import patch, MagicMock

import pytest
import requests

from tools.weather_tool import WeatherTools, _FORECAST_URL, _WEATHER_URL


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def weather_tools():
    return WeatherTools(api_key="test_api_key_123")


@pytest.fixture
def forecast_api_response():
    """Realistic 5-day/3-hour forecast response (2 days, 4 entries each)."""
    return {
        "city": {"name": "Paris", "country": "FR"},
        "list": [
            {
                "dt_txt": "2026-03-20 06:00:00",
                "main": {"temp": 8.5, "humidity": 72},
                "wind": {"speed": 3.2},
                "weather": [{"main": "Clouds"}],
            },
            {
                "dt_txt": "2026-03-20 09:00:00",
                "main": {"temp": 10.2, "humidity": 65},
                "wind": {"speed": 4.1},
                "weather": [{"main": "Clouds"}],
            },
            {
                "dt_txt": "2026-03-20 12:00:00",
                "main": {"temp": 13.8, "humidity": 55},
                "wind": {"speed": 5.0},
                "weather": [{"main": "Clear"}],
            },
            {
                "dt_txt": "2026-03-20 15:00:00",
                "main": {"temp": 14.1, "humidity": 50},
                "wind": {"speed": 4.5},
                "weather": [{"main": "Clear"}],
            },
            {
                "dt_txt": "2026-03-21 06:00:00",
                "main": {"temp": 7.0, "humidity": 80},
                "wind": {"speed": 6.1},
                "weather": [{"main": "Rain"}],
            },
            {
                "dt_txt": "2026-03-21 09:00:00",
                "main": {"temp": 8.5, "humidity": 85},
                "wind": {"speed": 7.2},
                "weather": [{"main": "Rain"}],
            },
            {
                "dt_txt": "2026-03-21 12:00:00",
                "main": {"temp": 9.0, "humidity": 82},
                "wind": {"speed": 5.5},
                "weather": [{"main": "Rain"}],
            },
            {
                "dt_txt": "2026-03-21 15:00:00",
                "main": {"temp": 9.5, "humidity": 78},
                "wind": {"speed": 4.8},
                "weather": [{"main": "Drizzle"}],
            },
        ],
    }


@pytest.fixture
def current_weather_response():
    """Realistic current weather response for historical estimates."""
    return {
        "name": "London",
        "sys": {"country": "GB"},
        "coord": {"lat": 51.5, "lon": -0.13},
        "main": {"temp": 12.5, "humidity": 70},
        "weather": [{"main": "Clouds", "description": "overcast clouds"}],
    }


def _mock_response(status_code=200, json_data=None):
    """Helper to create a mock requests.Response."""
    mock = MagicMock(spec=requests.Response)
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


# ── Toolkit registration ──────────────────────────────────────────────

class TestToolkitRegistration:
    def test_toolkit_has_name(self, weather_tools):
        assert weather_tools.name == "weather_tools"

    def test_api_key_stored(self, weather_tools):
        assert weather_tools.api_key == "test_api_key_123"

    def test_api_key_from_env(self):
        with patch.dict(os.environ, {"OPENWEATHERMAP_API_KEY": "env_key_456"}):
            tools = WeatherTools()
            assert tools.api_key == "env_key_456"

    def test_api_key_default_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENWEATHERMAP_API_KEY", None)
            tools = WeatherTools()
            assert tools.api_key == ""


# ── get_weather_forecast ──────────────────────────────────────────────

class TestGetWeatherForecast:
    def test_successful_forecast(self, weather_tools, forecast_api_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, forecast_api_response)

            result = json.loads(weather_tools.get_weather_forecast("Paris", 2))

            assert result["city"] == "Paris"
            assert result["country"] == "FR"
            assert len(result["forecasts"]) == 2
            mock_get.assert_called_once()

    def test_forecast_daily_aggregation(self, weather_tools, forecast_api_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, forecast_api_response)

            result = json.loads(weather_tools.get_weather_forecast("Paris", 2))
            day1 = result["forecasts"][0]

            assert day1["date"] == "2026-03-20"
            assert day1["temp_high_celsius"] == 14.1
            assert day1["temp_low_celsius"] == 8.5
            assert day1["humidity_percent"] is not None
            assert day1["wind_speed_ms"] is not None

    def test_forecast_outdoor_friendly_flag(self, weather_tools, forecast_api_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, forecast_api_response)

            result = json.loads(weather_tools.get_weather_forecast("Paris", 2))

            day1 = result["forecasts"][0]
            day2 = result["forecasts"][1]
            assert day1["is_outdoor_friendly"] is True
            assert day2["is_outdoor_friendly"] is False  # Rain day

    def test_forecast_city_not_found(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(404)

            result = json.loads(weather_tools.get_weather_forecast("NonexistentCity123", 3))
            assert "error" in result
            assert "not found" in result["error"].lower()

    def test_forecast_invalid_api_key(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(401)

            result = json.loads(weather_tools.get_weather_forecast("Paris", 3))
            assert "error" in result
            assert "Invalid" in result["error"]

    def test_forecast_server_error(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(500)

            result = json.loads(weather_tools.get_weather_forecast("Paris", 3))
            assert "error" in result
            assert "500" in result["error"]

    def test_forecast_timeout(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            result = json.loads(weather_tools.get_weather_forecast("Paris", 3))
            assert "error" in result
            assert "timed out" in result["error"].lower()

    def test_forecast_connection_error(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            result = json.loads(weather_tools.get_weather_forecast("Paris", 3))
            assert "error" in result
            assert "connect" in result["error"].lower()

    def test_forecast_no_api_key(self):
        tools = WeatherTools(api_key="")
        result = json.loads(tools.get_weather_forecast("Paris", 3))
        assert "error" in result
        assert "not configured" in result["error"].lower()

    def test_forecast_days_capped_at_5(self, weather_tools, forecast_api_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, forecast_api_response)

            weather_tools.get_weather_forecast("Paris", 10)

            call_args = mock_get.call_args
            assert call_args[1]["params"]["cnt"] == 40  # 5 * 8

    def test_forecast_days_minimum_1(self, weather_tools, forecast_api_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, forecast_api_response)

            weather_tools.get_weather_forecast("Paris", -1)

            call_args = mock_get.call_args
            assert call_args[1]["params"]["cnt"] == 8  # 1 * 8

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

    def test_forecast_empty_list(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, {
                "city": {"name": "Empty", "country": "XX"},
                "list": [],
            })

            result = json.loads(weather_tools.get_weather_forecast("Empty", 3))
            assert result["forecasts"] == []

    def test_forecast_generic_exception(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = ValueError("unexpected")

            result = json.loads(weather_tools.get_weather_forecast("Paris", 3))
            assert "error" in result
            assert "unexpected" in result["error"]


# ── get_historical_weather ────────────────────────────────────────────

class TestGetHistoricalWeather:
    def test_successful_historical(self, weather_tools, current_weather_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, current_weather_response)

            result = json.loads(weather_tools.get_historical_weather("London", 7))

            assert result["city"] == "London"
            assert result["country"] == "GB"
            assert result["month"] == "July"
            assert "typical_high_celsius" in result
            assert "typical_low_celsius" in result
            assert "typical_conditions" in result
            assert "precipitation_likelihood" in result
            assert "packing_suggestions" in result
            assert isinstance(result["packing_suggestions"], list)
            assert "best_activities" in result
            assert isinstance(result["best_activities"], list)
            assert "note" in result

    def test_historical_city_not_found(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(404)

            result = json.loads(weather_tools.get_historical_weather("FakeCity", 6))
            assert "error" in result
            assert "not found" in result["error"].lower()

    def test_historical_invalid_month_too_high(self, weather_tools):
        result = json.loads(weather_tools.get_historical_weather("London", 13))
        assert "error" in result
        assert "Invalid month" in result["error"]

    def test_historical_invalid_month_zero(self, weather_tools):
        result = json.loads(weather_tools.get_historical_weather("London", 0))
        assert "error" in result
        assert "Invalid month" in result["error"]

    def test_historical_invalid_api_key(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(401)

            result = json.loads(weather_tools.get_historical_weather("London", 6))
            assert "error" in result
            assert "Invalid" in result["error"]

    def test_historical_timeout(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            result = json.loads(weather_tools.get_historical_weather("London", 6))
            assert "error" in result
            assert "timed out" in result["error"].lower()

    def test_historical_connection_error(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            result = json.loads(weather_tools.get_historical_weather("London", 6))
            assert "error" in result
            assert "connect" in result["error"].lower()

    def test_historical_no_api_key(self):
        tools = WeatherTools(api_key="")
        result = json.loads(tools.get_historical_weather("London", 6))
        assert "error" in result
        assert "not configured" in result["error"].lower()

    def test_historical_all_months_valid(self, weather_tools, current_weather_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, current_weather_response)

            for month in range(1, 13):
                result = json.loads(weather_tools.get_historical_weather("London", month))
                assert "error" not in result, f"Month {month} returned error"
                assert result["month"] is not None

    def test_historical_passes_correct_params(self, weather_tools, current_weather_response):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, current_weather_response)

            weather_tools.get_historical_weather("Berlin,DE", 8)

            mock_get.assert_called_once_with(
                _WEATHER_URL,
                params={
                    "q": "Berlin,DE",
                    "appid": "test_api_key_123",
                    "units": "metric",
                },
                timeout=10,
            )

    def test_historical_generic_exception(self, weather_tools):
        with patch("tools.weather_tool.requests.get") as mock_get:
            mock_get.side_effect = RuntimeError("boom")

            result = json.loads(weather_tools.get_historical_weather("London", 6))
            assert "error" in result
            assert "boom" in result["error"]


# ── _aggregate_forecast (internal) ───────────────────────────────────

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

    def test_limits_to_requested_days(self):
        data = {
            "list": [
                {
                    "dt_txt": f"2026-04-0{d} 12:00:00",
                    "main": {"temp": 20, "humidity": 50},
                    "wind": {"speed": 3},
                    "weather": [{"main": "Clear"}],
                }
                for d in range(1, 6)
            ],
        }

        result = WeatherTools._aggregate_forecast(data, 3)
        assert len(result) == 3

    def test_empty_list(self):
        result = WeatherTools._aggregate_forecast({"list": []}, 5)
        assert result == []


# ── _seasonal_offset (internal) ──────────────────────────────────────

class TestSeasonalOffset:
    def test_same_month_zero_offset(self):
        offset = WeatherTools._seasonal_offset(45.0, 6, 6)
        assert offset == 0.0

    def test_northern_summer_warmer_than_winter(self):
        summer_offset = WeatherTools._seasonal_offset(45.0, 7, 1)
        winter_offset = WeatherTools._seasonal_offset(45.0, 1, 7)
        assert summer_offset > 0
        assert winter_offset < 0

    def test_southern_hemisphere_reversed(self):
        offset_north = WeatherTools._seasonal_offset(45.0, 7, 3)
        offset_south = WeatherTools._seasonal_offset(-45.0, 7, 3)
        assert offset_north > 0
        assert offset_south < 0


# ── _classify_climate (internal) ─────────────────────────────────────

class TestClassifyClimate:
    def test_cold_climate(self):
        result = WeatherTools._classify_climate(-5, 60, 1)
        assert "Cold" in result["conditions"] or "snow" in result["conditions"].lower()
        assert len(result["packing"]) > 0
        assert len(result["activities"]) > 0

    def test_cool_climate(self):
        result = WeatherTools._classify_climate(10, 50, 4)
        assert "Cool" in result["conditions"] or "mild" in result["conditions"].lower()

    def test_warm_climate(self):
        result = WeatherTools._classify_climate(22, 40, 6)
        assert "Warm" in result["conditions"] or "pleasant" in result["conditions"].lower()

    def test_hot_climate(self):
        result = WeatherTools._classify_climate(35, 30, 7)
        assert "Hot" in result["conditions"]

    def test_tropical_monsoon(self):
        result = WeatherTools._classify_climate(32, 10, 7)
        assert "monsoon" in result["conditions"].lower() or "humid" in result["conditions"].lower()
        assert "High" in result["precipitation"]


# ── Integration: TravelTeam weather fallback ─────────────────────────

class TestTravelTeamWeatherFallback:
    @pytest.fixture(autouse=True)
    def _mock_streamlit(self):
        with patch("agents.travel_team.st") as mock_st:
            mock_st.session_state = MagicMock()
            yield mock_st

    @pytest.fixture
    def _mock_agno(self):
        with (
            patch("agents.travel_team.Agent") as mock_agent,
            patch("agents.travel_team.Team") as mock_team,
            patch("agents.travel_team.Groq") as mock_groq,
            patch("agents.travel_team.SqliteDb") as mock_db,
            patch("agents.research_agent.Agent") as _,
            patch("agents.research_agent.Groq") as _,
            patch("agents.itinerary_agent.Agent") as _,
            patch("agents.itinerary_agent.Groq") as _,
            patch("agents.budget_agent.Agent") as _,
            patch("agents.budget_agent.Groq") as _,
            patch("agents.local_expert_agent.Agent") as _,
            patch("agents.local_expert_agent.Groq") as _,
        ):
            mock_team_instance = MagicMock()
            mock_team.return_value = mock_team_instance
            mock_team_instance.run.return_value = MagicMock(content="Test plan output")
            yield {
                "agent": mock_agent,
                "team": mock_team,
                "team_instance": mock_team_instance,
            }

    def test_no_api_key_means_weather_unavailable(self, _mock_agno):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENWEATHERMAP_API_KEY", None)
            from agents.travel_team import TravelTeam

            team = TravelTeam(session_id="test")
            assert team.weather_available is False
            assert team._weather_tools is None

    def test_with_api_key_weather_available(self, _mock_agno):
        with patch.dict(os.environ, {"OPENWEATHERMAP_API_KEY": "test_key"}):
            from agents.travel_team import TravelTeam

            team = TravelTeam(session_id="test")
            assert team.weather_available is True
            assert team._weather_tools is not None

    def test_fallback_plan_generation_works(self, _mock_agno):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENWEATHERMAP_API_KEY", None)
            from agents.travel_team import TravelTeam

            team = TravelTeam(session_id="test")
            result = team.generate_travel_plan(
                "Paris", "London", "2026-04-01", "2026-04-05",
                "Moderate", ["Culture"], 5,
            )

            _mock_agno["team_instance"].run.assert_called_once()
            assert result is not None
