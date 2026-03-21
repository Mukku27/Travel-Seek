"""Tests for mcp_servers.config — API key loading and client factory."""

import os
from unittest.mock import patch, MagicMock

import pytest
import googlemaps.exceptions

from mcp_servers.config import (
    get_api_key,
    get_gmaps_client,
    GoogleAPIQuotaError,
    validate_google_maps_access,
)


def test_get_api_key_returns_key_when_set():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
        assert get_api_key() == "test_key_123"


def test_get_api_key_raises_when_missing():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("GOOGLE_MAPS_API_KEY", None)
        with pytest.raises(EnvironmentError, match="GOOGLE_MAPS_API_KEY is not set"):
            get_api_key()


def test_get_gmaps_client_creates_client():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key"}):
        with patch("googlemaps.Client") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = get_gmaps_client()
            mock_cls.assert_called_once_with(key="test_key")


def test_google_api_quota_error_is_exception():
    err = GoogleAPIQuotaError("Quota exceeded")
    assert isinstance(err, Exception)
    assert str(err) == "Quota exceeded"


def test_validate_google_maps_access_raises_for_request_denied():
    mock_client = MagicMock()
    mock_client.geocode.side_effect = googlemaps.exceptions.ApiError("REQUEST_DENIED")

    with patch("googlemaps.Client", return_value=mock_client):
        with pytest.raises(GoogleAPIQuotaError):
            validate_google_maps_access.__wrapped__("test_key")
