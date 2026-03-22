"""Tests for agents.budget_agent."""

import os
from unittest.mock import MagicMock, patch


def test_budget_agent_wires_travel_search_tool():
    with (
        patch("agents.budget_agent.Agent") as mock_agent,
        patch("agents.budget_agent.Groq"),
        patch("agents.budget_agent.TravelSearchTools") as mock_travel_tool,
        patch("agents.budget_agent.DuckDuckGoTools") as mock_ddg,
    ):
        from agents.budget_agent import create_budget_agent

        travel_tool = MagicMock(name="travel_tool")
        ddg_tool = MagicMock(name="ddg_tool")
        mock_travel_tool.return_value = travel_tool
        mock_ddg.return_value = ddg_tool
        create_budget_agent()

    kwargs = mock_agent.call_args.kwargs
    assert kwargs["tools"][0] is travel_tool
    assert kwargs["tools"][1] is ddg_tool
    instructions = "\n".join(kwargs["instructions"])
    assert "get_trip_price_estimates" in instructions
    assert "booking links" in instructions.lower()


def test_budget_agent_adds_tavily_when_enabled():
    with (
        patch.dict(os.environ, {"USE_TAVILY": "true"}, clear=True),
        patch("agents.budget_agent.Agent") as mock_agent,
        patch("agents.budget_agent.Groq"),
        patch("agents.budget_agent.TravelSearchTools") as mock_travel_tool,
        patch("agents.budget_agent.DuckDuckGoTools") as mock_ddg,
        patch("agents.budget_agent.TavilyTools") as mock_tavily,
    ):
        from agents.budget_agent import create_budget_agent

        mock_travel_tool.return_value = MagicMock(name="travel_tool")
        mock_ddg.return_value = MagicMock(name="ddg_tool")
        tavily_tool = MagicMock(name="tavily_tool")
        mock_tavily.return_value = tavily_tool
        create_budget_agent()

    tools = mock_agent.call_args.kwargs["tools"]
    assert tavily_tool in tools
