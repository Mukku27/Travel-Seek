"""
local_expert_agent.py

Provides insider tips, cultural context, and off-the-beaten-path experiences.
Uses DuckDuckGo for research, with optional Tavily integration for richer results.
"""

import os

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.tavily import TavilyTools


def create_local_expert_agent() -> Agent:
    tools = [DuckDuckGoTools()]
    if os.getenv("USE_TAVILY", "").lower() in ("1", "true", "yes"):
        tools.append(TavilyTools(search=True, max_tokens=8000, search_depth="advanced"))

    return Agent(
        name="Local Expert",
        role="Cultural and Local Knowledge Specialist",
        model=Groq(id="qwen/qwen3-32b"),
        tools=tools,
        instructions=[
            "You are a local expert with deep cultural knowledge.",
            "Provide insider tips that tourists typically miss:",
            "- Cultural etiquette and dos/don'ts",
            "- Useful local phrases in the native language",
            "- Off-the-beaten-path experiences and hidden gems",
            "- Common tourist scams and how to avoid them",
            "- Local food specialties and where to find them",
            "- Best neighborhoods to explore",
            "- Local festivals or events during the travel dates",
            "- Photography tips and best viewpoints",
            "Write in an engaging, friendly tone as if advising a friend.",
            "Format as markdown with clear categories.",
        ],
        markdown=True,
        debug_mode=True,
    )
