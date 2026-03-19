"""
itinerary_agent.py

Builds optimized day-by-day itineraries from research findings.
Optionally uses Google Directions via MCP tools for real travel-time data.
"""

from agno.agent import Agent
from agno.models.groq import Groq


def create_itinerary_agent(mcp_tools=None) -> Agent:
    tools: list = []
    if mcp_tools is not None:
        tools.append(mcp_tools)

    extra_instructions = []
    if mcp_tools is not None:
        extra_instructions = [
            "You have access to Google Directions API via MCP tools.",
            "Use get_directions to compute real travel times between locations.",
            "Include the actual distance and duration in the itinerary.",
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
