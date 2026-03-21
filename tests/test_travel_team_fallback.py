"""Tests for TravelTeam MCP fallback behaviour.

These tests verify that TravelTeam degrades gracefully when the
Google Maps API key is missing or when the MCP connection fails.
All heavy dependencies (Agno, Groq, Streamlit) are mocked.
"""

import os
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


@pytest.fixture(autouse=True)
def _mock_streamlit():
    """Prevent Streamlit calls from crashing tests."""
    with patch("agents.travel_team.st") as mock_st:
        mock_st.session_state = MagicMock()
        yield mock_st


@pytest.fixture
def _mock_agno():
    """Mock Agno Agent, Team, Groq to avoid real model calls."""
    with (
        patch("agents.travel_team.Agent") as mock_agent,
        patch("agents.travel_team.Team") as mock_team,
        patch("agents.travel_team.Groq") as mock_groq,
        patch("agents.travel_team.SqliteDb") as mock_db,
        patch("agents.research_agent.Agent") as _,
        patch("agents.research_agent.Groq") as _,
        patch("agents.itinerary_agent.Agent") as _,
        patch("agents.itinerary_agent.Groq") as _,
        patch("agents.budget_agent.Agent") as _,
        patch("agents.budget_agent.Groq") as _,
        patch("agents.local_expert_agent.Agent") as _,
        patch("agents.local_expert_agent.Groq") as _,
    ):
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.run.return_value = MagicMock(content="Test plan output")
        yield {
            "agent": mock_agent,
            "team": mock_team,
            "team_instance": mock_team_instance,
        }


def test_no_api_key_means_mcp_unavailable(_mock_agno):
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("GOOGLE_MAPS_API_KEY", None)
        from agents.travel_team import TravelTeam

        team = TravelTeam(session_id="test")
        assert team.mcp_available is False
        assert team._mcp_tools is None


def test_with_api_key_but_connection_fails(_mock_agno):
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key"}):
        with (
            patch("agents.travel_team.validate_google_maps_access"),
            patch("agents.travel_team.MCPTools") as mock_mcp_cls,
        ):
            mock_mcp = MagicMock()
            mock_mcp.connect = AsyncMock(side_effect=ConnectionError("fail"))
            mock_mcp_cls.return_value = mock_mcp

            from agents.travel_team import TravelTeam

            team = TravelTeam(session_id="test")
            assert team.mcp_available is False
            assert team._mcp_tools is None


def test_with_api_key_but_tools_never_initialize(_mock_agno):
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key"}):
        with (
            patch("agents.travel_team.validate_google_maps_access"),
            patch("agents.travel_team.MCPTools") as mock_mcp_cls,
        ):
            mock_mcp = MagicMock()
            mock_mcp.connect = AsyncMock(return_value=None)
            mock_mcp.initialized = False
            mock_mcp_cls.return_value = mock_mcp

            from agents.travel_team import TravelTeam

            team = TravelTeam(session_id="test")
            assert team.mcp_available is False
            assert team._mcp_tools is None
            assert "failed during tool initialization" in team.mcp_status_reason.lower()


def test_fallback_uses_sync_run(_mock_agno):
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("GOOGLE_MAPS_API_KEY", None)
        from agents.travel_team import TravelTeam

        team = TravelTeam(session_id="test")

        result = team.generate_travel_plan(
            "Paris", "London", "2025-01-01", "2025-01-05",
            "Moderate", ["Culture"], 5,
        )

        _mock_agno["team_instance"].run.assert_called_once()
        assert result is not None


def test_disconnect_mcp_is_safe_when_not_connected(_mock_agno):
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("GOOGLE_MAPS_API_KEY", None)
        from agents.travel_team import TravelTeam

        team = TravelTeam(session_id="test")
        team.disconnect_mcp()  # should not raise
        assert team.mcp_available is False
