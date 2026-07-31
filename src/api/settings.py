"""Configuration settings for the Pro Vision Engine API."""

from dataclasses import dataclass


DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
)


@dataclass(frozen=True, slots=True)
class ApiSettings:
    """Contains configurable values for the web API."""

    title: str = "Pro Vision Engine API"
    version: str = "0.1.0-alpha"
    description: str = (
        "Football pool coupon import, validation "
        "and analysis API for Project 13."
    )
    service_name: str = "pro-vision-engine"
    allowed_origins: tuple[str, ...] = (
        DEFAULT_ALLOWED_ORIGINS
    )