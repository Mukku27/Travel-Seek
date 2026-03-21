"""Optional live integration tests for OpenWeatherMap.

These tests are skipped unless RUN_LIVE_WEATHER_TESTS=1 and
OPENWEATHERMAP_API_KEY is available in the environment.
"""

import json
import os
from datetime import date, timedelta

from dotenv import load_dotenv
import pytest

from tools.weather_tool import WeatherTools

load_dotenv()

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_WEATHER_TESTS") != "1" or not os.getenv("OPENWEATHERMAP_API_KEY"),
    reason="Set RUN_LIVE_WEATHER_TESTS=1 and OPENWEATHERMAP_API_KEY to run live tests.",
)


def test_live_current_weather():
    result = json.loads(WeatherTools().get_current_weather("Paris"))
    assert "error" not in result
    assert result["city"].lower() == "paris"
    assert result["current_temperature_celsius"] is not None


def test_live_trip_weather_guidance_with_exact_dates():
    start = (date.today() + timedelta(days=1)).isoformat()
    end = (date.today() + timedelta(days=2)).isoformat()

    result = json.loads(WeatherTools().get_trip_weather_guidance("Paris", start, end))
    assert "error" not in result
    assert result["exact_forecast_available"] is True
    assert len(result["forecasts"]) >= 1


def test_live_trip_weather_guidance_long_range_limit():
    start = (date.today() + timedelta(days=10)).isoformat()
    end = (date.today() + timedelta(days=11)).isoformat()

    result = json.loads(WeatherTools().get_trip_weather_guidance("Paris", start, end))
    assert "error" not in result
    assert result["exact_forecast_available"] is False
    assert result["missing_dates"]
