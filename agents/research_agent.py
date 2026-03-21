"""
research_agent.py

Gathers comprehensive destination information using DuckDuckGo search.
Optionally uses Tavily for higher-quality general web results when
USE_TAVILY is set, and optionally uses Google Places MCP tools when
the travel team can connect to the local Places server. When
OpenWeather tools are available, it uses them for verified trip-date
weather guidance instead of general web estimates.
"""

import os

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.tavily import TavilyTools


def create_research_agent(mcp_tools=None, weather_tools=None) -> Agent:
    use_tavily = os.getenv("USE_TAVILY", "false").lower() in ("true", "1", "yes")

    tools: list = [DuckDuckGoTools()]
    if use_tavily:
        tools.append(TavilyTools(search=True, max_tokens=8000, search_depth="advanced"))
    if mcp_tools is not None:
        tools.append(mcp_tools)
    if weather_tools is not None:
        tools.append(weather_tools)

    extra_instructions = []
    if use_tavily:
        extra_instructions.append(
            "Use Tavily when you need stronger web research for current travel information."
        )
    if mcp_tools is not None:
        extra_instructions.extend([
            "You have access to Google Places API tools via MCP.",
            "Prefer search_places and get_place_details for attraction data such as ratings, reviews, hours, and addresses.",
            "Use DuckDuckGo or Tavily for broader topics like visa and safety guidance.",
        ])
    if weather_tools is not None:
        extra_instructions.extend([
            "You have access to OpenWeatherMap weather tools.",
            "Use get_trip_weather_guidance for trip-specific weather.",
            "If get_trip_weather_guidance says exact forecast dates are unavailable, say that clearly and do not invent day-level weather.",
            "When exact forecast dates are unavailable, do not add historical averages or seasonal ranges unless you first verify them with a cited web source.",
            "If you do not have a cited long-range weather source, limit the weather section to the OpenWeather limitation note, current conditions, packing guidance, and when to recheck.",
            "Without a cited long-range weather source, do not include numeric temperature ranges or rainfall claims for those future dates.",
            "Prefer the packing_guidance returned by get_trip_weather_guidance instead of inventing your own weather-dependent packing details.",
            "Use get_current_weather for current conditions when it helps travelers decide when to visit.",
            "Use get_weather_forecast for generic near-term 1-5 day forecasts.",
            "Include packing suggestions only when they follow from weather tool output or verified sources.",
        ])

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
            "Never invent visa rules, accommodation prices, transport schedules, or weather details that were not verified by a tool or a cited source.",
            "Present findings in well-organized markdown with clear sections.",
            "Focus on accuracy over volume - only include verified information.",
            *extra_instructions,
        ],
        markdown=True,
        debug_mode=True,
    )
