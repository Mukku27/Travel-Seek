"""
research_agent.py

Gathers comprehensive destination information using DuckDuckGo search
and optionally Google Places data via MCP tools.
"""

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools


def create_research_agent(mcp_tools=None) -> Agent:
    tools: list = [DuckDuckGoTools()]
    if mcp_tools is not None:
        tools.append(mcp_tools)

    extra_instructions = []
    if mcp_tools is not None:
        extra_instructions = [
            "You have access to Google Places API tools via MCP.",
            "Prefer search_places and get_place_details for attraction data (ratings, reviews, hours).",
            "Fall back to DuckDuckGo for general info like weather, visa, and safety.",
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
