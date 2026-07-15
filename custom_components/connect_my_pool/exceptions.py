"""Typed exceptions for the Connect My Pool integration."""

from __future__ import annotations


class ConnectMyPoolError(Exception):
    """Base exception for Connect My Pool API errors."""


class ConnectMyPoolConnectionError(ConnectMyPoolError):
    """Raised when the API cannot be reached."""


class ConnectMyPoolAuthenticationError(ConnectMyPoolError):
    """Raised for invalid API code or API key (failure codes 3, 5)."""


class ConnectMyPoolApiNotEnabledError(ConnectMyPoolError):
    """Raised when the pool's API access has not been enabled (failure code 4)."""


class ConnectMyPoolRateLimitError(ConnectMyPoolError):
    """Raised when the 60 s throttle is exceeded (failure code 6)."""


class ConnectMyPoolNotConnectedError(ConnectMyPoolError):
    """Raised when the pool system is not connected (failure code 7)."""


class ConnectMyPoolActionError(ConnectMyPoolError):
    """Raised when an action fails with a specific failure code."""

    def __init__(self, failure_code: int, description: str) -> None:
        super().__init__(description)
        self.failure_code = failure_code
