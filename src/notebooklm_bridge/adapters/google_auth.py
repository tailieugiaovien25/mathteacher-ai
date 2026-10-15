"""Authentication boundary for Google integrations.

This module contains only the authentication contract.
It does not implement Google credentials or network access.
"""

from __future__ import annotations

from typing import Protocol


class GoogleAuthProvider(Protocol):
    """Contract for obtaining an access token."""

    def get_access_token(self) -> str:
        """Return an access token for an authorized Google API call."""
        ...
