"""
FastMCP server exposing Google Places and Directions tools.

Run standalone:
    python mcp_servers/places_server.py              # stdio (default)
    python mcp_servers/places_server.py --transport sse --port 8000
"""

import json
import sys
from typing import Optional

from fastmcp import FastMCP

from mcp_servers.config import get_gmaps_client
from mcp_servers.places_tools import (
    search_places as _search_places,
    get_place_details as _get_place_details,
    get_directions as _get_directions,
)

mcp = FastMCP(name="travel-seek-places")


@mcp.tool
def search_places(
    query: str,
    location: str,
    radius: int = 5000,
    type: str = "tourist_attraction",
) -> str:
    """Search for places near a location using Google Places API.

    Args:
        query: Search keyword (e.g. "museums", "restaurants").
        location: Human-readable location string (e.g. "Paris, France").
        radius: Search radius in metres (default 5000).
        type: Google place type filter (default "tourist_attraction").

    Returns:
        JSON array of up to 5 places with name, rating, address, etc.
    """
    client = get_gmaps_client()
    results = _search_places(client, query, location, radius, place_type=type)
    return json.dumps(results, indent=2)


@mcp.tool
def get_place_details(place_id: str) -> str:
    """Get detailed information about a specific place.

    Args:
        place_id: Google Maps place_id obtained from search_places.

    Returns:
        JSON object with name, rating, phone, website, hours, reviews, etc.
    """
    client = get_gmaps_client()
    result = _get_place_details(client, place_id)
    return json.dumps(result, indent=2)


@mcp.tool
def get_directions(
    origin: str,
    destination: str,
    mode: str = "transit",
) -> str:
    """Get directions between two locations.

    Args:
        origin: Starting location (e.g. "Eiffel Tower, Paris").
        destination: Ending location (e.g. "Louvre Museum, Paris").
        mode: Travel mode — one of "driving", "walking", "bicycling", "transit".

    Returns:
        JSON object with total distance, duration, and step-by-step directions.
    """
    client = get_gmaps_client()
    result = _get_directions(client, origin, destination, mode=mode)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    transport = "stdio"
    port = 8000
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--transport" and i + 1 < len(args):
            transport = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        else:
            i += 1

    if transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        mcp.run()
