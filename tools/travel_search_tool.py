"""
travel_search_tool.py

SerpApi-backed toolkit for Google Flights and Google Hotels estimates.
The toolkit returns normalized JSON that budget agents can use directly
for tiered travel-cost breakdowns with booking links.
"""

import json
import os
import re
from datetime import date
from statistics import median
from typing import Optional

import requests
from agno.tools import Toolkit

_SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
_REQUEST_TIMEOUT_SECONDS = 15
_DEFAULT_MAX_RESULTS = 5


class TravelSearchTools(Toolkit):
    """Toolkit exposing normalized SerpApi flight and hotel estimate tools."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = os.getenv("SERPI_API_KEY", "") if api_key is None else api_key
        super().__init__(
            name="travel_search_tools",
            tools=[
                self.search_flights,
                self.search_hotels,
                self.get_trip_price_estimates,
            ],
        )

    # ── Public tools ──────────────────────────────────────────────

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        currency: str = "USD",
        travel_class: str = "economy",
        max_results: int = _DEFAULT_MAX_RESULTS,
    ) -> str:
        """Search Google Flights via SerpApi and return normalized options."""
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "adults": max(adults, 1),
            "currency": currency.upper(),
            "travel_class": travel_class.lower(),
            "hl": "en",
        }
        if return_date:
            params["return_date"] = return_date

        raw = self._serpapi_request(params)
        if "error" in raw:
            return json.dumps(raw)

        source_url = raw.get("search_metadata", {}).get("google_flights_url")
        flights = self._normalize_flights(raw, source_url, max_results=max_results)

        return json.dumps(
            {
                "source": "SerpApi Google Flights",
                "source_url": source_url,
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "currency": currency.upper(),
                "flight_options": flights,
            },
            indent=2,
        )

    def search_hotels(
        self,
        destination: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 1,
        currency: str = "USD",
        max_results: int = _DEFAULT_MAX_RESULTS,
    ) -> str:
        """Search Google Hotels via SerpApi and return normalized options."""
        params = {
            "engine": "google_hotels",
            "q": destination,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "adults": max(adults, 1),
            "currency": currency.upper(),
            "hl": "en",
            "gl": "us",
        }

        raw = self._serpapi_request(params)
        if "error" in raw:
            return json.dumps(raw)

        source_url = raw.get("search_metadata", {}).get("google_hotels_url")
        hotels = self._normalize_hotels(raw, fallback_link=source_url, max_results=max_results)

        return json.dumps(
            {
                "source": "SerpApi Google Hotels",
                "source_url": source_url,
                "destination": destination,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "currency": currency.upper(),
                "hotel_options": hotels,
            },
            indent=2,
        )

    def get_trip_price_estimates(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        adults: int = 1,
        currency: str = "USD",
    ) -> str:
        """Get combined flight + accommodation estimates for budget planning."""
        date_error = self._validate_date_window(departure_date, return_date)
        if date_error is not None:
            return json.dumps({"error": date_error})

        normalized_adults = max(adults, 1)
        nights = max((date.fromisoformat(return_date) - date.fromisoformat(departure_date)).days, 1)

        flights_raw = self._serpapi_request(
            {
                "engine": "google_flights",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": departure_date,
                "return_date": return_date,
                "adults": normalized_adults,
                "currency": currency.upper(),
                "travel_class": "economy",
                "hl": "en",
            },
        )
        if "error" in flights_raw:
            return json.dumps(flights_raw)

        hotels_raw = self._serpapi_request(
            {
                "engine": "google_hotels",
                "q": destination,
                "check_in_date": departure_date,
                "check_out_date": return_date,
                "adults": normalized_adults,
                "currency": currency.upper(),
                "hl": "en",
                "gl": "us",
            },
        )
        if "error" in hotels_raw:
            return json.dumps(hotels_raw)

        flight_source_url = flights_raw.get("search_metadata", {}).get("google_flights_url")
        hotel_source_url = hotels_raw.get("search_metadata", {}).get("google_hotels_url")
        flights = self._normalize_flights(flights_raw, flight_source_url, max_results=_DEFAULT_MAX_RESULTS)
        hotels = self._normalize_hotels(hotels_raw, fallback_link=hotel_source_url, max_results=_DEFAULT_MAX_RESULTS)

        flight_prices = [item["price_value"] for item in flights if item["price_value"] is not None]
        hotel_prices = [item["nightly_rate_value"] for item in hotels if item["nightly_rate_value"] is not None]

        budget_flight, mid_flight, luxury_flight = self._tier_values(flight_prices)
        budget_hotel, mid_hotel, luxury_hotel = self._tier_values(hotel_prices)

        tiers = {
            "budget": self._build_tier_estimate(
                flight_price=budget_flight,
                hotel_nightly=budget_hotel,
                nights=nights,
                travelers=normalized_adults,
                currency=currency.upper(),
            ),
            "mid_range": self._build_tier_estimate(
                flight_price=mid_flight,
                hotel_nightly=mid_hotel,
                nights=nights,
                travelers=normalized_adults,
                currency=currency.upper(),
            ),
            "luxury": self._build_tier_estimate(
                flight_price=luxury_flight,
                hotel_nightly=luxury_hotel,
                nights=nights,
                travelers=normalized_adults,
                currency=currency.upper(),
            ),
        }

        return json.dumps(
            {
                "source": "SerpApi Google Flights + Google Hotels",
                "currency": currency.upper(),
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "travelers": normalized_adults,
                "nights": nights,
                "tier_estimates": tiers,
                "flight_options": flights,
                "hotel_options": hotels,
                "booking_links": {
                    "flights": [item["booking_url"] for item in flights if item.get("booking_url")],
                    "hotels": [item["booking_url"] for item in hotels if item.get("booking_url")],
                },
                "source_urls": [url for url in [flight_source_url, hotel_source_url] if url],
            },
            indent=2,
        )

    # ── Private helpers ───────────────────────────────────────────

    def _serpapi_request(self, params: dict) -> dict:
        if not self.api_key:
            return {"error": "SERPI_API_KEY is not configured."}

        try:
            response = requests.get(
                _SERPAPI_SEARCH_URL,
                params={**params, "api_key": self.api_key},
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.Timeout:
            return {"error": "SerpApi request timed out."}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to SerpApi."}
        except requests.exceptions.HTTPError as exc:
            return {"error": f"SerpApi request failed: {exc}"}
        except Exception as exc:
            return {"error": f"SerpApi request failed: {exc}"}

        if isinstance(payload, dict) and payload.get("error"):
            return {"error": f"SerpApi error: {payload['error']}"}
        return payload if isinstance(payload, dict) else {"error": "Unexpected SerpApi response format."}

    @staticmethod
    def _normalize_flights(payload: dict, fallback_link: Optional[str], max_results: int) -> list[dict]:
        options: list[dict] = []
        for item in payload.get("best_flights", []) + payload.get("other_flights", []):
            price_text = item.get("price")
            legs = item.get("flights", [])
            airlines = sorted({leg.get("airline", "").strip() for leg in legs if leg.get("airline")})
            first_leg = legs[0] if legs else {}
            last_leg = legs[-1] if legs else {}
            departure = first_leg.get("departure_airport", {})
            arrival = last_leg.get("arrival_airport", {})

            options.append(
                {
                    "price_text": price_text,
                    "price_value": TravelSearchTools._extract_price_value(price_text),
                    "airlines": airlines,
                    "total_duration": item.get("total_duration"),
                    "departure_airport": departure.get("name") or departure.get("id"),
                    "arrival_airport": arrival.get("name") or arrival.get("id"),
                    "departure_time": departure.get("time"),
                    "arrival_time": arrival.get("time"),
                    "stops": max(len(legs) - 1, 0),
                    "booking_url": item.get("booking_url")
                    or item.get("link")
                    or fallback_link,
                },
            )

        return TravelSearchTools._rank_by_price(options, "price_value", max_results)

    @staticmethod
    def _normalize_hotels(payload: dict, fallback_link: Optional[str], max_results: int) -> list[dict]:
        options: list[dict] = []
        for item in payload.get("properties", []):
            nightly = item.get("rate_per_night", {}).get("lowest")
            if nightly is None:
                nightly = item.get("rate_per_night", {}).get("extracted_lowest")
            total = item.get("total_rate", {}).get("lowest")
            if total is None:
                total = item.get("total_rate", {}).get("extracted_lowest")
            options.append(
                {
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "rating": item.get("overall_rating") or item.get("rating"),
                    "reviews": item.get("reviews"),
                    "nightly_rate_text": nightly,
                    "nightly_rate_value": TravelSearchTools._extract_price_value(nightly),
                    "total_rate_text": total,
                    "total_rate_value": TravelSearchTools._extract_price_value(total),
                    "booking_url": item.get("link") or item.get("booking_link") or fallback_link,
                },
            )
        return TravelSearchTools._rank_by_price(options, "nightly_rate_value", max_results)

    @staticmethod
    def _extract_price_value(raw_value) -> Optional[float]:
        if raw_value is None:
            return None
        if isinstance(raw_value, (int, float)):
            return float(raw_value)

        match = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(raw_value))
        if not match:
            return None
        return float(match.group(0).replace(",", ""))

    @staticmethod
    def _rank_by_price(options: list[dict], price_key: str, max_results: int) -> list[dict]:
        ranked = sorted(
            options,
            key=lambda item: item[price_key] if item[price_key] is not None else float("inf"),
        )
        return ranked[: max(max_results, 1)]

    @staticmethod
    def _validate_date_window(start_date: str, end_date: str) -> Optional[str]:
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError:
            return "Dates must use ISO format YYYY-MM-DD."
        if end < start:
            return "return_date must be on or after departure_date."
        return None

    @staticmethod
    def _tier_values(values: list[float]) -> tuple[Optional[float], Optional[float], Optional[float]]:
        if not values:
            return None, None, None
        sorted_values = sorted(values)
        return (
            sorted_values[0],
            float(median(sorted_values)),
            sorted_values[-1],
        )

    @staticmethod
    def _build_tier_estimate(
        flight_price: Optional[float],
        hotel_nightly: Optional[float],
        nights: int,
        travelers: int,
        currency: str,
    ) -> dict:
        flight_total = flight_price * travelers if flight_price is not None else None
        hotel_total = hotel_nightly * nights if hotel_nightly is not None else None

        estimated_total = None
        if flight_total is not None and hotel_total is not None:
            estimated_total = round(flight_total + hotel_total, 2)

        return {
            "currency": currency,
            "flight_per_person": flight_price,
            "flight_total_for_travelers": round(flight_total, 2) if flight_total is not None else None,
            "hotel_nightly_rate": hotel_nightly,
            "hotel_total_for_stay": round(hotel_total, 2) if hotel_total is not None else None,
            "estimated_total": estimated_total,
        }
