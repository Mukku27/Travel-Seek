"""
weather_tool.py

Agno Toolkit that wraps the OpenWeatherMap API to provide:
  - current weather
  - 5-day weather forecasts (aggregated to daily summaries)
  - trip-date guidance that explains when exact forecast coverage is unavailable

Gracefully degrades when the API key is missing or calls fail.
"""

import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import requests
from dotenv import load_dotenv

from agno.tools import Toolkit

_BASE_URL = "https://api.openweathermap.org"
_FORECAST_URL = f"{_BASE_URL}/data/2.5/forecast"
_WEATHER_URL = f"{_BASE_URL}/data/2.5/weather"

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_REQUEST_TIMEOUT = 10
_FORECAST_MAX_DAYS = 5
_CURRENT_SOURCE_URL = "https://openweathermap.org/current"
_FORECAST_SOURCE_URL = "https://openweathermap.org/forecast5"

load_dotenv()


class WeatherTools(Toolkit):
    """OpenWeatherMap toolkit for travel weather intelligence."""

    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY", "") if api_key is None else api_key
        super().__init__(
            name="weather_tools",
            tools=[
                self.get_current_weather,
                self.get_weather_forecast,
                self.get_trip_weather_guidance,
            ],
        )

    # ── Public tools ──────────────────────────────────────────────

    def get_current_weather(self, city: str) -> str:
        """Get the current weather for a city."""
        data = self._fetch_current_weather(city)
        if "error" in data:
            return json.dumps(data)

        return json.dumps(
            {
                "city": data.get("name", city),
                "country": data.get("sys", {}).get("country", ""),
                "source": "OpenWeather current weather",
                "source_url": _CURRENT_SOURCE_URL,
                **self._format_current_conditions(data),
            },
            indent=2,
        )

    def get_weather_forecast(self, city: str, days: int = 5) -> str:
        """Get a daily weather forecast for a city (up to 5 days)."""
        days = max(1, min(days, _FORECAST_MAX_DAYS))
        data = self._fetch_forecast(city, days * 8)
        if "error" in data:
            return json.dumps(data)

        daily = self._aggregate_forecast(data, days)
        return json.dumps(
            {
                "city": data.get("city", {}).get("name", city),
                "country": data.get("city", {}).get("country", ""),
                "source": "OpenWeather 5-day / 3-hour forecast",
                "source_url": _FORECAST_SOURCE_URL,
                "forecast_window_start": daily[0]["date"] if daily else None,
                "forecast_window_end": daily[-1]["date"] if daily else None,
                "forecasts": daily,
            },
            indent=2,
        )

    def get_trip_weather_guidance(self, city: str, start_date: str, end_date: str) -> str:
        """Get verified weather guidance for a specific trip date range.

        Returns exact daily forecasts only for dates covered by the OpenWeather
        5-day forecast endpoint. When a requested date falls outside that
        supported window, the response makes the limitation explicit instead of
        inventing weather conditions.
        """
        if not self.api_key:
            return json.dumps({"error": "OpenWeatherMap API key is not configured."})

        try:
            trip_start = date.fromisoformat(start_date)
            trip_end = date.fromisoformat(end_date)
        except ValueError:
            return json.dumps(
                {"error": "Dates must use ISO format YYYY-MM-DD."},
            )

        if trip_end < trip_start:
            return json.dumps(
                {"error": "end_date must be on or after start_date."},
            )

        current = self._fetch_current_weather(city)
        if "error" in current:
            return json.dumps(current)

        forecast = self._fetch_forecast(city, _FORECAST_MAX_DAYS * 8)
        if "error" in forecast:
            return json.dumps(forecast)

        daily = self._aggregate_forecast(forecast, None)
        daily_by_date = {item["date"]: item for item in daily}
        requested_dates = [
            (trip_start + timedelta(days=offset)).isoformat()
            for offset in range((trip_end - trip_start).days + 1)
        ]
        matched = [daily_by_date[day] for day in requested_dates if day in daily_by_date]
        missing = [day for day in requested_dates if day not in daily_by_date]
        forecast_window_start = daily[0]["date"] if daily else None
        forecast_window_end = daily[-1]["date"] if daily else None

        response = {
            "city": current.get("name", city),
            "country": current.get("sys", {}).get("country", ""),
            "requested_start_date": trip_start.isoformat(),
            "requested_end_date": trip_end.isoformat(),
            "forecast_window_start": forecast_window_start,
            "forecast_window_end": forecast_window_end,
            "exact_forecast_available": not missing,
            "forecasts": matched,
            "missing_dates": missing,
            "current_conditions": self._format_current_conditions(current),
            "packing_guidance": self._build_packing_guidance(matched, not missing),
            "source_urls": [_CURRENT_SOURCE_URL, _FORECAST_SOURCE_URL],
        }

        if missing:
            response["note"] = (
                "Exact OpenWeather daily forecasts are only available within the next 5 days "
                "with the configured subscription. Do not infer weather for missing dates."
            )
            recheck_date = max(date.today(), trip_start - timedelta(days=_FORECAST_MAX_DAYS))
            response["recommended_recheck_date"] = recheck_date.isoformat()
        else:
            response["note"] = (
                "These daily summaries are derived from OpenWeather 3-hour forecast data."
            )

        return json.dumps(response, indent=2)

    def get_historical_weather(self, city: str, month: int) -> str:
        """Return an honest limitation message for unsupported monthly history."""
        if not 1 <= month <= 12:
            return json.dumps({"error": f"Invalid month: {month}. Must be 1-12."})

        current = self._fetch_current_weather(city)
        if "error" in current:
            return json.dumps(current)

        return json.dumps(
            {
                "city": current.get("name", city),
                "country": current.get("sys", {}).get("country", ""),
                "requested_month": month,
                "requested_month_name": _MONTH_NAMES[month],
                "supported": False,
                "note": (
                    "Monthly historical normals and long-range daily forecasts are not "
                    "available through the configured OpenWeather subscription. Use "
                    "get_trip_weather_guidance within five days of travel for exact dates."
                ),
                "current_conditions": self._format_current_conditions(current),
                "source_url": _CURRENT_SOURCE_URL,
            },
            indent=2,
        )

    # ── Private helpers ───────────────────────────────────────────

    def _fetch_current_weather(self, city: str) -> dict:
        if not self.api_key:
            return {"error": "OpenWeatherMap API key is not configured."}

        return self._request_json(
            _WEATHER_URL,
            {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
            },
            city,
        )

    def _fetch_forecast(self, city: str, count: int) -> dict:
        if not self.api_key:
            return {"error": "OpenWeatherMap API key is not configured."}

        return self._request_json(
            _FORECAST_URL,
            {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "cnt": count,
            },
            city,
        )

    @staticmethod
    def _format_current_conditions(data: dict) -> dict:
        weather = data.get("weather", [{}])[0]
        observed_at = data.get("dt")
        observed_at_iso = None
        if observed_at:
            observed_at_iso = datetime.fromtimestamp(
                observed_at,
                tz=timezone.utc,
            ).isoformat()

        return {
            "current_temperature_celsius": data.get("main", {}).get("temp"),
            "feels_like_celsius": data.get("main", {}).get("feels_like"),
            "humidity_percent": data.get("main", {}).get("humidity"),
            "wind_speed_ms": data.get("wind", {}).get("speed"),
            "condition": weather.get("main"),
            "description": weather.get("description"),
            "observed_at_utc": observed_at_iso,
        }

    @staticmethod
    def _request_json(url: str, params: dict, city: str) -> dict:
        try:
            resp = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT)

            if resp.status_code == 404:
                return {"error": f"City not found: {city}"}
            if resp.status_code == 401:
                return {"error": "Invalid OpenWeatherMap API key."}
            if resp.status_code != 200:
                return {"error": f"Weather API error (HTTP {resp.status_code})"}

            return resp.json()
        except requests.exceptions.Timeout:
            return {"error": "Weather API request timed out."}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to Weather API."}
        except Exception as exc:
            return {"error": f"Weather API request failed: {str(exc)}"}

    @staticmethod
    def _build_packing_guidance(forecasts: list[dict], exact_forecast_available: bool) -> list[str]:
        if not exact_forecast_available or not forecasts:
            return [
                "Layered clothing for variable conditions",
                "A light waterproof layer or umbrella",
                "Comfortable walking shoes",
            ]

        guidance = {"Comfortable walking shoes"}
        highs = [item["temp_high_celsius"] for item in forecasts if item["temp_high_celsius"] is not None]
        lows = [item["temp_low_celsius"] for item in forecasts if item["temp_low_celsius"] is not None]
        conditions = {item["condition"] for item in forecasts}

        if lows and min(lows) < 10:
            guidance.add("A light jacket or warm layers for cooler mornings and evenings")
        if highs and max(highs) >= 22:
            guidance.add("Sun protection such as sunglasses or sunscreen")
        if {"Rain", "Drizzle", "Thunderstorm"} & conditions:
            guidance.add("A waterproof jacket or umbrella")
        else:
            guidance.add("Light layers for mild daytime temperatures")

        return sorted(guidance)

    @staticmethod
    def _aggregate_forecast(data: dict, days: Optional[int]) -> list[dict]:
        """Collapse 3-hour forecast intervals into daily summaries."""
        daily_buckets: dict[str, list[dict]] = defaultdict(list)

        for entry in data.get("list", []):
            date_str = entry.get("dt_txt", "")[:10]
            daily_buckets[date_str].append(entry)

        forecasts = []
        date_keys = sorted(daily_buckets.keys())
        if days is not None:
            date_keys = date_keys[:days]

        for date_str in date_keys:
            entries = daily_buckets[date_str]
            temps = [e["main"]["temp"] for e in entries if "main" in e]
            humidities = [e["main"]["humidity"] for e in entries if "main" in e]
            winds = [e["wind"]["speed"] for e in entries if "wind" in e]

            conditions = []
            for entry in entries:
                for weather in entry.get("weather", []):
                    conditions.append(weather.get("main", ""))

            most_common = max(set(conditions), key=conditions.count) if conditions else "Unknown"

            forecasts.append({
                "date": date_str,
                "temp_high_celsius": round(max(temps), 1) if temps else None,
                "temp_low_celsius": round(min(temps), 1) if temps else None,
                "condition": most_common,
                "humidity_percent": round(sum(humidities) / len(humidities)) if humidities else None,
                "wind_speed_ms": round(sum(winds) / len(winds), 1) if winds else None,
                "is_outdoor_friendly": most_common not in ("Rain", "Thunderstorm", "Snow", "Drizzle"),
            })

        return forecasts
