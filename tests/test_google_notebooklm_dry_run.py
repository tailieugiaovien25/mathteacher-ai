from __future__ import annotations

import unittest

from notebooklm_bridge.adapters.google_auth import GoogleAuthProvider
from notebooklm_bridge.adapters.google_notebooklm import (
    GoogleNotebookLMClient,
    GoogleNotebookLMConfig,
)
from notebooklm_bridge.adapters.notebooklm import (
    NotebookLMAdapter,
    NotebookLMAdapterConfig,
)


class FakeAuthProvider:
    def __init__(self) -> None:
        self.calls = 0

    def get_access_token(self) -> str:
        self.calls += 1
        return "fake-access-token"


class DryRunGoogleNotebookLMClient(GoogleNotebookLMClient):
    """Local-only client: never performs network access."""

    def __init__(
        self,
        config: GoogleNotebookLMConfig,
        auth_provider: GoogleAuthProvider,
    ) -> None:
        super().__init__(
            config=config,
            auth_provider=auth_provider,
        )
        self.calls: list[tuple[str, str]] = []

    def sync_source(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> str:
        if self.network_enabled:
            raise AssertionError(
                "Dry-run client must never enable network access"
            )

        self.calls.append((notebook_id, document_id))

        # Verify the authentication boundary without using
        # any real Google credential.
        token = self.get_access_token_for_request()

        if token != "fake-access-token":
            raise AssertionError(
                "Unexpected dry-run authentication token"
            )

        return (
            f"dry-run-source/"
            f"{notebook_id}/"
            f"{document_id}"
        )


class TestGoogleNotebookLMDryRun(unittest.TestCase):

    def test_adapter_to_google_client_end_to_end(self) -> None:
        auth = FakeAuthProvider()

        client = DryRunGoogleNotebookLMClient(
            config=GoogleNotebookLMConfig(
                project_id="mathteacher-test",
                location="us-central1",
                network_enabled=False,
            ),
            auth_provider=auth,
        )

        adapter = NotebookLMAdapter(
            config=NotebookLMAdapterConfig(
                enabled=True,
            ),
            client=client,
        )

        result = adapter.sync_source(
            notebook_id="notebook-001",
            document_id="document-001",
        )

        self.assertEqual(
            result,
            "dry-run-source/notebook-001/document-001",
        )

        self.assertEqual(
            client.calls,
            [
                ("notebook-001", "document-001"),
            ],
        )

        self.assertEqual(auth.calls, 1)
        self.assertFalse(client.network_enabled)

    def test_resource_name_is_preserved(self) -> None:
        auth = FakeAuthProvider()

        client = DryRunGoogleNotebookLMClient(
            config=GoogleNotebookLMConfig(
                project_id="mathteacher-test",
                location="us-central1",
                network_enabled=False,
            ),
            auth_provider=auth,
        )

        self.assertEqual(
            client.build_notebook_resource_name(
                notebook_id="notebook-001",
            ),
            (
                "projects/mathteacher-test/"
                "locations/us-central1/"
                "notebooks/notebook-001"
            ),
        )

        self.assertFalse(client.network_enabled)


if __name__ == "__main__":
    unittest.main()
