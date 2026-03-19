"""
itinerary_agent.py

Builds optimized day-by-day itineraries from research findings.
When weather tools are available, adjusts indoor/outdoor recommendations
based on real forecast data.
"""

from agno.agent import Agent
from agno.models.groq import Groq


def create_itinerary_agent(weather_tools=None) -> Agent:
    tools: list = []
    if weather_tools is not None:
        tools.append(weather_tools)

    extra_instructions = []
    if weather_tools is not None:
        extra_instructions = [
            "You have access to OpenWeatherMap weather tools.",
            "Use get_weather_forecast to check weather conditions for each day of the trip.",
            "Include a brief weather summary (temp, condition) at the top of each day's plan.",
            "Schedule indoor activities (museums, galleries, shopping) on rainy or extreme weather days.",
            "Recommend outdoor activities (parks, walking tours, beaches) on clear and pleasant days.",
            "Add packing suggestions at the end based on the overall weather forecast.",
        ]

    return Agent(
        name="Itinerary Planner",
        role="Day-by-Day Itinerary Specialist",
        model=Groq(id="qwen/qwen3-32b"),
        tools=tools if tools else [],
        instructions=[
            "You are an expert itinerary planner.",
            "Using the research data provided, create optimized day-by-day travel plans.",
            "For each day include:",
            "- Morning, afternoon, and evening activities with specific time slots",
            "- Estimated travel time between locations",
            "- Meal recommendations at appropriate times",
            "- Rainy day backup alternatives",
            "Optimize routes to minimize travel time between activities.",
            "Balance packed sightseeing with downtime based on travel style.",
            "Format as clear markdown with day headers and time-based schedules.",
            *extra_instructions,
        ],
        markdown=True,
        debug_mode=True,
    )
