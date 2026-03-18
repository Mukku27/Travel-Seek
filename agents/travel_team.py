"""
travel_team.py

Team orchestrator that coordinates the 4 specialized agents.
Delegation order: Research -> Itinerary -> Budget -> Local Expert -> compile.
"""

import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from agno.team.team import Team

from agents.research_agent import create_research_agent
from agents.itinerary_agent import create_itinerary_agent
from agents.budget_agent import create_budget_agent
from agents.local_expert_agent import create_local_expert_agent
from prompt import get_travel_plan_prompt, get_answer_question_prompt
from utils import clean_response


class TravelTeam:
    """Orchestrates 4 specialized travel agents via an Agno Team."""

    def __init__(self):
        self.research_agent = create_research_agent()
        self.itinerary_agent = create_itinerary_agent()
        self.budget_agent = create_budget_agent()
        self.local_expert_agent = create_local_expert_agent()

        self.team = Team(
            name="Travel Planning Team",
            mode="coordinate",
            model=Groq(id="deepseek-r1-distill-llama-70b"),
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
            ],
            show_tool_calls=True,
            markdown=True,
        )

    def generate_travel_plan(
        self, destination, present_location, start_date, end_date,
        budget, travel_style, duration,
    ):
        prompt = get_travel_plan_prompt(
            destination, present_location, start_date, end_date,
            budget, travel_style, duration,
        )
        response = self.team.run(prompt)
        try:
            if hasattr(response, "content"):
                clean_resp = clean_response(response.content)
            else:
                clean_resp = clean_response(str(response))
            st.session_state.travel_plan = clean_resp
            return clean_resp
        except Exception as e:
            st.error(f"Error generating travel plan: {str(e)}")
            return None

    def answer_question(self, question, travel_plan, destination):
        prompt = get_answer_question_prompt(destination, travel_plan, question)
        response = self.team.run(prompt)
        try:
            if hasattr(response, "content"):
                return clean_response(response.content)
            return clean_response(str(response))
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            return None
