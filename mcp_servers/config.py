"""
MCP server configuration and Google Maps API client factory.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class GoogleAPIQuotaError(Exception):
    """Raised when Google API returns OVER_QUERY_LIMIT or REQUEST_DENIED."""


def get_api_key() -> str:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        raise EnvironmentError(
            "GOOGLE_MAPS_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable."
        )
    return key


def get_gmaps_client():
    """Return a configured googlemaps.Client instance."""
    import googlemaps

    return googlemaps.Client(key=get_api_key())


@lru_cache(maxsize=4)
def validate_google_maps_access(api_key: str) -> None:
    """Fail fast when the configured key cannot reach the required Maps APIs."""
    import googlemaps

    client = googlemaps.Client(key=api_key)
    try:
        client.geocode("Paris, France")
    except googlemaps.exceptions.ApiError as exc:
        msg = str(exc).upper()
        if "OVER_QUERY_LIMIT" in msg or "REQUEST_DENIED" in msg:
            raise GoogleAPIQuotaError(str(exc)) from exc
        raise RuntimeError(f"Google Maps validation failed: {exc}") from exc
    except googlemaps.exceptions.Timeout as exc:
        raise RuntimeError(f"Google Maps validation timed out: {exc}") from exc
