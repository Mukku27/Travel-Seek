"""
itinerary_agent.py

Builds optimized day-by-day itineraries from research findings.
Optionally uses Google Directions via MCP tools for real travel-time data
and OpenWeather tools for verified trip-date weather guidance.
"""

from agno.agent import Agent
from agno.models.groq import Groq


def create_itinerary_agent(mcp_tools=None, weather_tools=None) -> Agent:
    tools: list = []
    if mcp_tools is not None:
        tools.append(mcp_tools)
    if weather_tools is not None:
        tools.append(weather_tools)

    extra_instructions = []
    if mcp_tools is not None:
        extra_instructions.extend([
            "You have access to Google Directions API via MCP tools.",
            "Use get_directions to compute real travel times between locations.",
            "Include the actual distance and duration in the itinerary.",
        ])
    if weather_tools is not None:
        extra_instructions.extend([
            "You have access to OpenWeatherMap weather tools.",
            "Use get_trip_weather_guidance for trip-date weather checks.",
            "Only include a day-specific weather summary when get_trip_weather_guidance returns an exact forecast for that date.",
            "If the response says exact forecast dates are unavailable, say that clearly and do not invent day-level weather.",
            "Schedule indoor activities (museums, galleries, shopping) on rainy or extreme weather days.",
            "Recommend outdoor activities (parks, walking tours, beaches) on clear and pleasant days.",
            "Add packing suggestions at the end based on the overall weather forecast.",
        ])

    return Agent(
        name="Itinerary Planner",
        role="Day-by-Day Itinerary Specialist",
        model=Groq(id="qwen/qwen3-32b"),
        tools=tools if tools else [],
        instructions=[
            "You are an expert itinerary planner.",
            "Using the research data provided, create optimized day-by-day travel plans.",
            "Use only attractions, prices, opening-status notes, and transport facts that were provided in the research data or returned by Google Directions tools.",
            "If a detail is not verified, say to confirm it on the official site instead of guessing.",
            "For each day include:",
            "- Morning, afternoon, and evening activities with specific time slots",
            "- Estimated travel time between locations",
            "- Meal recommendations at appropriate times",
            "- Rainy day backup alternatives",
            "Optimize routes to minimize travel time between activities.",
            "Balance packed sightseeing with downtime based on travel style.",
            "When Google Directions is unavailable, use qualitative phrasing like 'short metro ride' or 'walkable' instead of inventing exact routes, line names, or station names.",
            "Format as clear markdown with day headers and time-based schedules.",
            *extra_instructions,
        ],
        markdown=True,
        debug_mode=True,
    )
