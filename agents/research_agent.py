"""
research_agent.py

Gathers comprehensive destination information using DuckDuckGo search.
Researches weather, safety, visa requirements, attractions, restaurants,
local transport, currency, and tipping culture.
"""

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools


def create_research_agent() -> Agent:
    return Agent(
        name="Research Agent",
        role="Destination Research Specialist",
        model=Groq(id="qwen/qwen3-32b"),
        tools=[DuckDuckGoTools()],
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
        ],
        markdown=True,
        debug_mode=True,
    )
