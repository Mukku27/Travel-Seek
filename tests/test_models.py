"""Tests for models.UserPreferences."""

from models import UserPreferences


def test_default_preferences():
    prefs = UserPreferences()
    assert prefs.destination is None
    assert prefs.num_days is None
    assert prefs.travel_style == []
    assert prefs.special_requirements == []


def test_summary_no_prefs():
    prefs = UserPreferences()
    assert prefs.summary() == "No preferences set yet."


def test_summary_with_prefs():
    prefs = UserPreferences(
        destination="Tokyo",
        num_days=5,
        budget_tier="Moderate",
        travel_style=["Culture", "Food"],
    )
    summary = prefs.summary()
    assert "Tokyo" in summary
    assert "5" in summary
    assert "Moderate" in summary
    assert "Culture" in summary
    assert "Food" in summary


def test_update_from_merges_non_none():
    prefs = UserPreferences(destination="Paris", num_days=3)
    other = UserPreferences(num_days=7, budget_tier="Luxury")

    prefs.update_from(other)

    assert prefs.destination == "Paris"  # unchanged
    assert prefs.num_days == 7  # updated
    assert prefs.budget_tier == "Luxury"  # new


def test_update_from_ignores_empty_list():
    prefs = UserPreferences(travel_style=["Nature"])
    other = UserPreferences(travel_style=[])

    prefs.update_from(other)
    assert prefs.travel_style == ["Nature"]


def test_update_from_replaces_non_empty_list():
    prefs = UserPreferences(travel_style=["Nature"])
    other = UserPreferences(travel_style=["Culture", "Food"])

    prefs.update_from(other)
    assert prefs.travel_style == ["Culture", "Food"]


def test_update_from_ignores_none():
    prefs = UserPreferences(destination="Rome")
    other = UserPreferences()

    prefs.update_from(other)
    assert prefs.destination == "Rome"


def test_model_validate_json():
    raw = '{"destination": "Berlin", "num_days": 4}'
    prefs = UserPreferences.model_validate_json(raw)
    assert prefs.destination == "Berlin"
    assert prefs.num_days == 4
    assert prefs.budget_tier is None
