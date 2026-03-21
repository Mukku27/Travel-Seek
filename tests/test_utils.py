"""Tests for utils.clean_response."""

from utils import clean_response


def test_strips_think_tags():
    text = "<think>internal reasoning</think>Hello world"
    assert clean_response(text) == "Hello world"


def test_strips_think_tags_multiline():
    text = "<think>\nlong\nreasoning\n</think>\n\nActual content"
    result = clean_response(text)
    assert "think" not in result
    assert "Actual content" in result


def test_replaces_special_pipe_char():
    text = "Column A ∣ Column B"
    assert clean_response(text) == "Column A | Column B"


def test_collapses_triple_newlines():
    text = "Line 1\n\n\nLine 2"
    assert clean_response(text) == "Line 1\n\nLine 2"


def test_strips_surrounding_whitespace():
    text = "   Hello   "
    assert clean_response(text) == "Hello"


def test_empty_string():
    assert clean_response("") == ""


def test_only_think_tags():
    assert clean_response("<think>stuff</think>") == ""


def test_complex_mixed_content():
    text = "<think>ignore</think>  Title ∣ Value\n\n\nBody  "
    result = clean_response(text)
    assert result == "Title | Value\n\nBody"
