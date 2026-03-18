"""
budget_agent.py

Estimates costs across budget tiers and suggests money-saving alternatives.
Uses DuckDuckGo for price lookups.
"""

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools


def create_budget_agent() -> Agent:
    return Agent(
        name="Budget Analyst",
        role="Travel Budget and Cost Specialist",
        model=Groq(id="deepseek-r1-distill-llama-70b"),
        tools=[DuckDuckGoTools()],
        instructions=[
            "You are a travel budget analyst.",
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
            "Format as markdown with comparison tables where appropriate.",
        ],
        show_tool_calls=True,
        markdown=True,
    )
