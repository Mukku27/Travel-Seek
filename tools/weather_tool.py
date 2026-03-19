"""
weather_tool.py

Agno Toolkit that wraps the OpenWeatherMap free-tier API to provide:
  - 5-day weather forecasts (aggregated to daily summaries)
  - Historical monthly climate averages for longer-range trip planning

Gracefully degrades when the API key is missing or calls fail.
"""

import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Optional

import requests

from agno.tools import Toolkit

_BASE_URL = "https://api.openweathermap.org"
_FORECAST_URL = f"{_BASE_URL}/data/2.5/forecast"
_WEATHER_URL = f"{_BASE_URL}/data/2.5/weather"
_GEO_URL = f"{_BASE_URL}/geo/1.0/direct"

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_REQUEST_TIMEOUT = 10


class WeatherTools(Toolkit):
    """OpenWeatherMap toolkit for travel weather intelligence."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY", "")
        super().__init__(
            name="weather_tools",
            tools=[self.get_weather_forecast, self.get_historical_weather],
        )

    # ── Public tools ──────────────────────────────────────────────

    def get_weather_forecast(self, city: str, days: int = 5) -> str:
        """Get a daily weather forecast for a city (up to 5 days).

        Args:
            city: City name, optionally with country code (e.g. "Paris" or "Tokyo,JP").
            days: Number of forecast days (1-5, capped at 5 for the free tier).

        Returns:
            JSON string with a list of daily forecasts containing date, temperature
            (high/low in Celsius), condition, humidity, and wind speed.
        """
        if not self.api_key:
            return json.dumps({"error": "OpenWeatherMap API key is not configured."})

        days = max(1, min(days, 5))

        try:
            resp = requests.get(
                _FORECAST_URL,
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                    "cnt": days * 8,  # 8 data points per day (3-hour intervals)
                },
                timeout=_REQUEST_TIMEOUT,
            )

            if resp.status_code == 404:
                return json.dumps({"error": f"City not found: {city}"})
            if resp.status_code == 401:
                return json.dumps({"error": "Invalid OpenWeatherMap API key."})
            if resp.status_code != 200:
                return json.dumps({"error": f"Weather API error (HTTP {resp.status_code})"})

            data = resp.json()
            daily = self._aggregate_forecast(data, days)
            return json.dumps({
                "city": data.get("city", {}).get("name", city),
                "country": data.get("city", {}).get("country", ""),
                "forecasts": daily,
            }, indent=2)

        except requests.exceptions.Timeout:
            return json.dumps({"error": "Weather API request timed out."})
        except requests.exceptions.ConnectionError:
            return json.dumps({"error": "Could not connect to Weather API."})
        except Exception as exc:
            return json.dumps({"error": f"Weather forecast error: {str(exc)}"})

    def get_historical_weather(self, city: str, month: int) -> str:
        """Get typical monthly weather for a city to help plan future trips.

        Uses current conditions as a baseline and provides general climate
        context for the requested month. Best for trips planned beyond the
        5-day forecast window.

        Args:
            city: City name, optionally with country code (e.g. "London,GB").
            month: Month number (1-12).

        Returns:
            JSON string with typical temperature ranges, conditions, and
            packing recommendations for the given month.
        """
        if not self.api_key:
            return json.dumps({"error": "OpenWeatherMap API key is not configured."})

        if not 1 <= month <= 12:
            return json.dumps({"error": f"Invalid month: {month}. Must be 1-12."})

        try:
            resp = requests.get(
                _WEATHER_URL,
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                },
                timeout=_REQUEST_TIMEOUT,
            )

            if resp.status_code == 404:
                return json.dumps({"error": f"City not found: {city}"})
            if resp.status_code == 401:
                return json.dumps({"error": "Invalid OpenWeatherMap API key."})
            if resp.status_code != 200:
                return json.dumps({"error": f"Weather API error (HTTP {resp.status_code})"})

            data = resp.json()
            coords = data.get("coord", {})
            month_name = _MONTH_NAMES[month]

            current_temp = data.get("main", {}).get("temp", 20)
            current_month = datetime.now().month
            temp_offset = self._seasonal_offset(coords.get("lat", 0), month, current_month)

            estimated_temp = round(current_temp + temp_offset, 1)
            estimated_high = round(estimated_temp + 5, 1)
            estimated_low = round(estimated_temp - 5, 1)

            climate = self._classify_climate(estimated_temp, coords.get("lat", 0), month)

            return json.dumps({
                "city": data.get("name", city),
                "country": data.get("sys", {}).get("country", ""),
                "month": month_name,
                "note": "Estimates based on current conditions and seasonal patterns. Check closer to your trip for precise forecasts.",
                "typical_high_celsius": estimated_high,
                "typical_low_celsius": estimated_low,
                "typical_conditions": climate["conditions"],
                "precipitation_likelihood": climate["precipitation"],
                "packing_suggestions": climate["packing"],
                "best_activities": climate["activities"],
            }, indent=2)

        except requests.exceptions.Timeout:
            return json.dumps({"error": "Weather API request timed out."})
        except requests.exceptions.ConnectionError:
            return json.dumps({"error": "Could not connect to Weather API."})
        except Exception as exc:
            return json.dumps({"error": f"Historical weather error: {str(exc)}"})

    # ── Private helpers ───────────────────────────────────────────

    @staticmethod
    def _aggregate_forecast(data: dict, days: int) -> list[dict]:
        """Collapse 3-hour forecast intervals into daily summaries."""
        daily_buckets: dict[str, list[dict]] = defaultdict(list)

        for entry in data.get("list", []):
            date_str = entry.get("dt_txt", "")[:10]
            daily_buckets[date_str].append(entry)

        forecasts = []
        for date_str in sorted(daily_buckets.keys())[:days]:
            entries = daily_buckets[date_str]
            temps = [e["main"]["temp"] for e in entries if "main" in e]
            humidities = [e["main"]["humidity"] for e in entries if "main" in e]
            winds = [e["wind"]["speed"] for e in entries if "wind" in e]

            conditions = []
            for e in entries:
                for w in e.get("weather", []):
                    conditions.append(w.get("main", ""))

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

    @staticmethod
    def _seasonal_offset(lat: float, target_month: int, current_month: int) -> float:
        """Rough temperature offset between current month and target month.

        Uses latitude to determine hemisphere and applies a simplified
        sinusoidal seasonal model.
        """
        import math

        northern = lat >= 0
        if northern:
            warmest, coldest = 7, 1
        else:
            warmest, coldest = 1, 7

        def _seasonal_score(m: int) -> float:
            peak = warmest
            return math.cos(math.pi * (m - peak) / 6)

        delta = _seasonal_score(target_month) - _seasonal_score(current_month)
        amplitude = 15 if abs(lat) > 35 else 8
        return delta * amplitude

    @staticmethod
    def _classify_climate(temp: float, lat: float, month: int) -> dict:
        """Generate weather context, packing tips, and activity suggestions."""
        packing = []
        activities = []

        if temp < 5:
            conditions = "Cold, possible snow"
            precipitation = "Moderate (snow likely)"
            packing = ["Heavy winter coat", "Thermal layers", "Warm boots", "Gloves and hat", "Scarf"]
            activities = ["Museums", "Indoor markets", "Hot springs", "Winter sports"]
        elif temp < 15:
            conditions = "Cool and mild"
            precipitation = "Moderate"
            packing = ["Layered clothing", "Light jacket", "Comfortable walking shoes", "Umbrella"]
            activities = ["Walking tours", "Parks and gardens", "Cultural sites", "Local cafes"]
        elif temp < 25:
            conditions = "Warm and pleasant"
            precipitation = "Low to moderate"
            packing = ["Light layers", "Sunscreen", "Sunglasses", "Comfortable shoes", "Light rain jacket"]
            activities = ["Outdoor sightseeing", "Hiking", "Beach visits", "Outdoor dining"]
        else:
            conditions = "Hot"
            precipitation = "Low (unless tropical)"
            packing = ["Light breathable clothing", "Sun hat", "Sunscreen SPF 50+", "Water bottle", "Sandals"]
            activities = ["Early morning tours", "Water activities", "Indoor attractions midday", "Evening walks"]

            if abs(lat) < 25 and month in (6, 7, 8, 9, 12, 1, 2):
                conditions = "Hot and humid, possible monsoon"
                precipitation = "High"
                packing.append("Waterproof bag")
                packing.append("Quick-dry clothing")

        return {
            "conditions": conditions,
            "precipitation": precipitation,
            "packing": packing,
            "activities": activities,
        }
