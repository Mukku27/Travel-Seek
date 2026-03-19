"""
research_agent.py

Gathers comprehensive destination information using DuckDuckGo search.
Researches weather, safety, visa requirements, attractions, restaurants,
local transport, currency, and tipping culture.

When weather tools are available, provides real forecast data and
packing suggestions based on actual conditions.
"""

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools


def create_research_agent(weather_tools=None) -> Agent:
    tools: list = [DuckDuckGoTools()]
    if weather_tools is not None:
        tools.append(weather_tools)

    extra_instructions = []
    if weather_tools is not None:
        extra_instructions = [
            "You have access to OpenWeatherMap weather tools.",
            "Use get_weather_forecast to provide a real 5-day weather forecast for the destination.",
            "Use get_historical_weather for trips beyond 5 days to show typical monthly weather.",
            "Include packing suggestions based on the weather data returned by these tools.",
            "Present a per-day weather summary (temperature, condition, indoor/outdoor suitability).",
        ]

    return Agent(
        name="Research Agent",
        role="Destination Research Specialist",
        model=Groq(id="qwen/qwen3-32b"),
        tools=tools,
        instructions=[
            "You are a destination research specialist.",
            "Your job is to gather comprehensive, factual information about travel destinations.",
            "Research the following for every destination:",
            "- Current weather patterns and best time to visit",
            "- Safety advisories and visa requirements",
            "- Top attractions, restaurants, and hidden gems",
            "- Local transportation options and costs",
            "- Currency, tipping culture, and general cost of living",
            "- Cultural norms and etiquette",
            "Always cite your sources with working URLs.",
            "Present findings in well-organized markdown with clear sections.",
            "Focus on accuracy over volume - only include verified information.",
            *extra_instructions,
        ],
        markdown=True,
        debug_mode=True,
    )
