"""
MCP server configuration and Google Maps API client factory.
"""

import os
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
