"""
budget_agent.py

Estimates costs across budget tiers and suggests money-saving alternatives.
Uses SerpApi-backed flight/hotel pricing for grounded cost breakdowns.
"""

import os

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.tavily import TavilyTools
from tools import TravelSearchTools


def create_budget_agent() -> Agent:
    tools = [TravelSearchTools(), DuckDuckGoTools()]
    if os.getenv("USE_TAVILY", "").lower() in ("1", "true", "yes"):
        tools.append(TavilyTools())

    return Agent(
        name="Budget Analyst",
        role="Travel Budget and Cost Specialist",
        model=Groq(id="qwen/qwen3-32b"),
        tools=tools,
        instructions=[
            "You are a travel budget analyst.",
            "Always call get_trip_price_estimates first when origin, destination, and travel dates are available.",
            "Use the returned flight_options and hotel_options as the primary source for accommodation and intercity transport pricing.",
            "Include booking links from booking_links in the final output.",
            "If the pricing tool is unavailable or missing required inputs, clearly explain what is missing and what needs manual verification.",
            "Provide detailed cost estimates for the travel plan across three tiers:",
            "- Budget: hostels, street food, public transport",
            "- Mid-range: 3-star hotels, casual dining, mix of transport",
            "- Luxury: 5-star hotels, fine dining, private transfers",
            "For each tier, break down costs by:",
            "- Accommodation (per night and total)",
            "- Food (per day and total)",
            "- Transportation (local and intercity)",
            "- Activities and entrance fees",
            "- Miscellaneous and emergency fund",
            "Include money-saving tips specific to the destination.",
            "Provide currency conversion rates where relevant.",
            "Keep prices grounded in tool outputs and do not invent exact rates.",
            "Format as markdown with comparison tables where appropriate.",
        ],
        markdown=True,
        debug_mode=True,
    )
