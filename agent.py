"""
agent.py

This module manages the AI agent logic. It wraps the interactions with the AI model, including response 
generation and decision-making. The TravelAgent class uses prompt functions from prompt.py to generate the required prompts.
"""

import streamlit as st
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.serpapi_tools import SerpApiTools
from phi.tools.duckduckgo import DuckDuckGo
from prompt import get_travel_plan_prompt, get_answer_question_prompt
from utils import clean_response

class TravelAgent:
    """
    TravelAgent encapsulates the logic for interacting with the AI model and generating travel plans 
    or answering questions.
    """
    def __init__(self):
        self.agent = Agent(
            name="Comprehensive Travel Assistant",
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            tools=[SerpApiTools(), DuckDuckGo()],
            instructions=[
                "You are a comprehensive travel planning assistant with expertise in all aspects of travel.",
                "For every recommendation and data point, you MUST provide working source links.",
                "Your knowledge spans across:",
                "- Seasonal travel timing and weather patterns",
                "- Transportation options and booking",
                "- Accommodation recommendations",
                "- Day-by-day itinerary planning",
                "- Local cuisine and restaurant recommendations",
                "- Practical travel tips and cultural advice",
                "- Budget estimation and cost breakdown",
                "Format all responses in markdown with clear headings (##) and bullet points.",
                "Use [text](url) format for all hyperlinks.",
                "Verify all links are functional before including them.",
                "Organize information clearly with appropriate sections based on the query type."
            ],
            show_tool_calls=True,
            markdown=True,
            debug_mode=True
        )

    def generate_travel_plan(self, destination, present_location, start_date, end_date, budget, travel_style, duration):
        """
        Generate a travel plan using the AI agent.
        """
        prompt = get_travel_plan_prompt(destination, present_location, start_date, end_date, budget, travel_style, duration)
        response = self.agent.run(prompt)
        try:
            if hasattr(response, 'content'):
                clean_resp = clean_response(response.content)
                st.session_state.travel_plan = clean_resp
                return clean_resp
            else:
                st.session_state.travel_plan = str(response)
                return str(response)
        except Exception as e:
            st.error(f"Error generating travel plan: {str(e)}")
            return None

    def answer_question(self, question, travel_plan, destination):
        """
        Answer a specific question based on the existing travel plan.
        """
        prompt = get_answer_question_prompt(destination, travel_plan, question)
        response = self.agent.run(prompt)
        try:
            if hasattr(response):
                return clean_response(response)
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            return None
