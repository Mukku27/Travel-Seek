"""
travel_team.py

Team orchestrator that coordinates the 4 specialized agents.
Supports multi-turn conversational planning with session memory
persisted in SQLite.

When GOOGLE_MAPS_API_KEY is available, the Research and Itinerary agents
gain access to Google Places / Directions tools via a custom MCP server.
If the key is missing or the MCP connection fails, the team falls back
gracefully to DuckDuckGo-only mode.
"""

import asyncio
import json
import os
import re
import sys

import nest_asyncio
import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from agno.team.team import Team
from agno.tools.mcp import MCPTools
from agno.db.sqlite.sqlite import SqliteDb

from agents.research_agent import create_research_agent
from agents.itinerary_agent import create_itinerary_agent
from agents.budget_agent import create_budget_agent
from agents.local_expert_agent import create_local_expert_agent
from models import UserPreferences
from prompt import get_travel_plan_prompt, get_answer_question_prompt
from utils import clean_response

nest_asyncio.apply()

DB_FILE = "tmp/travel_sessions.db"


def _run_async(coro):
    """Bridge helper: run an async coroutine from synchronous code."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class TravelTeam:
    """Orchestrates 4 specialized travel agents via an Agno Team with session memory."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.db = SqliteDb(db_file=DB_FILE)
        self.mcp_available = False
        self._mcp_tools: MCPTools | None = None

        has_key = bool(os.getenv("GOOGLE_MAPS_API_KEY"))
        if has_key:
            try:
                self._mcp_tools = self._connect_mcp()
                self.mcp_available = True
            except Exception:
                self.mcp_available = False
                self._mcp_tools = None

        mcp = self._mcp_tools if self.mcp_available else None
        self.research_agent = create_research_agent(mcp_tools=mcp)
        self.itinerary_agent = create_itinerary_agent(mcp_tools=mcp)
        self.budget_agent = create_budget_agent()
        self.local_expert_agent = create_local_expert_agent()

        self.team = Team(
            name="Travel Planning Team",
            mode="coordinate",
            model=Groq(id="qwen/qwen3-32b"),
            members=[
                self.research_agent,
                self.itinerary_agent,
                self.budget_agent,
                self.local_expert_agent,
            ],
            instructions=[
                "You are the lead coordinator of a travel planning team.",
                "Delegate tasks to your team members in this order:",
                "1. Research Agent: Gather destination data (weather, safety, attractions, transport)",
                "2. Itinerary Planner: Build a day-by-day plan from the research",
                "3. Budget Analyst: Estimate costs and provide budget tiers",
                "4. Local Expert: Add insider tips and cultural context",
                "After all agents respond, compile their outputs into one cohesive travel plan.",
                "Ensure no duplicate information across sections.",
                "Format the final output in clean markdown with clear section headers.",
                "When the user asks to modify the plan, only update the relevant sections.",
                "Always consider the accumulated user preferences and conversation history.",
            ],
            session_id=session_id,
            db=self.db,
            add_history_to_context=True,
            num_history_runs=10,
            markdown=True,
            show_members_responses=True,
            debug_mode=True,
        )

        self.preference_extractor = Agent(
            name="Preference Extractor",
            model=Groq(id="qwen/qwen3-32b"),
            instructions=[
                "Extract travel preferences from the user message.",
                "Return ONLY valid JSON with these fields (omit fields not mentioned):",
                '  destination, num_days, budget_tier, travel_style (list), group_size, special_requirements (list), home_currency',
                "Examples:",
                '  "I want to visit Tokyo for 3 days" -> {"destination": "Tokyo", "num_days": 3}',
                '  "Make it luxury and add vegetarian food" -> {"budget_tier": "Luxury", "special_requirements": ["vegetarian"]}',
                "Return ONLY the JSON object, no explanation, no markdown fences.",
            ],
            markdown=False,
        )

    # ── MCP lifecycle ──────────────────────────────────────────────

    def _connect_mcp(self) -> MCPTools:
        """Create and connect MCPTools to the places MCP server (stdio)."""
        server_cmd = f"{sys.executable} -m mcp_servers.places_server"
        mcp_tools = MCPTools(command=server_cmd)
        _run_async(mcp_tools.connect())
        return mcp_tools

    def disconnect_mcp(self) -> None:
        if self._mcp_tools is not None:
            try:
                _run_async(self._mcp_tools.close())
            except Exception:
                pass
            self._mcp_tools = None
            self.mcp_available = False

    # ── Private helpers ────────────────────────────────────────────

    def _run_team(self, prompt: str):
        """Run the team, with async bridge for MCP compatibility."""
        if self.mcp_available:
            return _run_async(self.team.arun(prompt))
        return self.team.run(prompt)

    def _extract_content(self, response) -> str:
        if hasattr(response, "content"):
            return clean_response(response.content)
        return clean_response(str(response))

    # ── Public API ─────────────────────────────────────────────────

    def extract_preferences(self, message: str, current_prefs: UserPreferences) -> UserPreferences:
        """Extract preferences from a user message and merge with existing ones."""
        try:
            response = self.preference_extractor.run(message)
            raw = response.content if hasattr(response, "content") else str(response)
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            extracted = UserPreferences.model_validate_json(raw)
            current_prefs.update_from(extracted)
        except Exception:
            pass
        return current_prefs

    def _build_context_prompt(self, message: str, preferences: UserPreferences) -> str:
        pref_summary = preferences.summary()
        return (
            f"## Current User Preferences\n{pref_summary}\n\n"
            f"## User Message\n{message}"
        )

    def generate_travel_plan(
        self, destination, present_location, start_date, end_date,
        budget, travel_style, duration,
    ):
        prompt = get_travel_plan_prompt(
            destination, present_location, start_date, end_date,
            budget, travel_style, duration,
        )
        try:
            response = self._run_team(prompt)
            clean_resp = self._extract_content(response)
            st.session_state.travel_plan = clean_resp
            return clean_resp
        except Exception as e:
            st.error(f"Error generating travel plan: {str(e)}")
            return None

    def chat(self, message: str, preferences: UserPreferences) -> str:
        """Handle a conversational message with context from preferences and history."""
        preferences = self.extract_preferences(message, preferences)
        prompt = self._build_context_prompt(message, preferences)
        try:
            response = self._run_team(prompt)
            return self._extract_content(response)
        except Exception as e:
            return f"Error: {str(e)}"

    def answer_question(self, question, travel_plan, destination):
        prompt = get_answer_question_prompt(destination, travel_plan, question)
        try:
            response = self._run_team(prompt)
            return self._extract_content(response)
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            return None
