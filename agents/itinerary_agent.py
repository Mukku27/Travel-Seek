"""
itinerary_agent.py

Builds optimized day-by-day itineraries from research findings.
No external tools - works purely from research data provided by the team.
"""

from agno.agent import Agent
from agno.models.groq import Groq


def create_itinerary_agent() -> Agent:
    return Agent(
        name="Itinerary Planner",
        role="Day-by-Day Itinerary Specialist",
        model=Groq(id="qwen/qwen3-32b"),
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
        ],
        markdown=True,
        debug_mode=True,
    )
