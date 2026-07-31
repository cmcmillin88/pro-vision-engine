"""Tests for the Pro Vision Engine API settings."""

from dataclasses import FrozenInstanceError

import pytest

from src.api.settings import (
    ApiSettings,
    DEFAULT_ALLOWED_ORIGINS,
)


def test_api_settings_have_expected_defaults() -> None:
    settings = ApiSettings()

    assert settings.title == "Pro Vision Engine API"
    assert settings.version == "0.1.0-alpha"
    assert settings.service_name == "pro-vision-engine"


def test_api_settings_include_local_origins() -> None:
    settings = ApiSettings()

    assert settings.allowed_origins == (
        DEFAULT_ALLOWED_ORIGINS
    )
    assert "http://localhost:5173" in (
        settings.allowed_origins
    )


def test_api_settings_are_immutable() -> None:
    settings = ApiSettings()

    with pytest.raises(FrozenInstanceError):
        setattr(
            settings,
            "title",
            "Changed title",
        )