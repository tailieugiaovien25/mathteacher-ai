"""Google NotebookLM official-client boundary.

STUB ONLY:
- no network calls
- no Google credentials
- no cookies/session tokens
- no private NotebookLM endpoints
"""

from __future__ import annotations

from dataclasses import dataclass

from notebooklm_bridge.adapters.google_auth import GoogleAuthProvider
from notebooklm_bridge.adapters.notebooklm_client import NotebookLMClient


@dataclass(frozen=True)
class GoogleNotebookLMConfig:
    project_id: str
    location: str
    network_enabled: bool = False


class GoogleNotebookLMClient(NotebookLMClient):
    """Configuration/authentication boundary for the official API."""

    def __init__(
        self,
        config: GoogleNotebookLMConfig,
        auth_provider: GoogleAuthProvider | None = None,
    ) -> None:
        if not config.project_id.strip():
            raise ValueError("project_id must not be empty")

        if not config.location.strip():
            raise ValueError("location must not be empty")

        self._config = config
        self._auth_provider = auth_provider

    @property
    def network_enabled(self) -> bool:
        return self._config.network_enabled

    @property
    def auth_provider(self) -> GoogleAuthProvider | None:
        return self._auth_provider

    def build_notebook_resource_name(
        self,
        *,
        notebook_id: str,
    ) -> str:
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        return (
            f"projects/{self._config.project_id}"
            f"/locations/{self._config.location}"
            f"/notebooks/{notebook_id}"
        )

    def get_access_token_for_request(self) -> str:
        """Obtain a token through the injected auth boundary.

        This STUB does not send the token anywhere.
        """

        if self._auth_provider is None:
            raise RuntimeError(
                "No Google authentication provider configured"
            )

        return self._auth_provider.get_access_token()

    def sync_source(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> str | None:
        raise NotImplementedError(
            "Official Google NotebookLM API client is not "
            "implemented in the STUB stage"
        )


__all__ = [
    "GoogleNotebookLMClient",
    "GoogleNotebookLMConfig",
]
