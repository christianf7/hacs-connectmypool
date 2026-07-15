"""Typed exceptions for the Astra Pool integration."""

from __future__ import annotations


class AstraPoolError(Exception):
    """Base exception for Astra Pool API errors."""


class AstraPoolConnectionError(AstraPoolError):
    """Raised when the API cannot be reached."""


class AstraPoolAuthenticationError(AstraPoolError):
    """Raised for invalid API code or API key (failure codes 3, 5)."""


class AstraPoolApiNotEnabledError(AstraPoolError):
    """Raised when the pool's API access has not been enabled (failure code 4)."""


class AstraPoolRateLimitError(AstraPoolError):
    """Raised when the 60 s throttle is exceeded (failure code 6)."""


class AstraPoolNotConnectedError(AstraPoolError):
    """Raised when the pool system is not connected (failure code 7)."""


class AstraPoolActionError(AstraPoolError):
    """Raised when an action fails with a specific failure code."""

    def __init__(self, failure_code: int, description: str) -> None:
        super().__init__(description)
        self.failure_code = failure_code
