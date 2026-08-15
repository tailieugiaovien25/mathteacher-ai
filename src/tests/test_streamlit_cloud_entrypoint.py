from pathlib import Path

from streamlit_app import (
    CLOUD_SECRET_NAMES,
    configure_python_path,
    configure_streamlit_secrets,
    copy_secrets_to_environment,
)


def test_cloud_entrypoint_adds_project_and_source_paths():
    search_path = []
    configure_python_path(
        project_root=Path("/app/mathteacher-ai"),
        source_root=Path("/app/mathteacher-ai/src"),
        search_path=search_path,
    )
    assert str(Path("/app/mathteacher-ai").resolve()) in search_path
    assert str(Path("/app/mathteacher-ai/src").resolve()) in search_path


def test_cloud_entrypoint_copies_only_known_secrets():
    environment = {"SUPABASE_URL": "keep-existing"}
    copy_secrets_to_environment(
        {
            "SUPABASE_URL": "replace-me",
            "SUPABASE_PUBLISHABLE_KEY": "publishable",
            "GOOGLE_OAUTH_CLIENT_ID": "client-id",
            "UNRELATED_SECRET": "must-not-copy",
        },
        environment,
    )
    assert environment["SUPABASE_URL"] == "keep-existing"
    assert environment["SUPABASE_PUBLISHABLE_KEY"] == "publishable"
    assert environment["GOOGLE_OAUTH_CLIENT_ID"] == "client-id"
    assert "UNRELATED_SECRET" not in environment
    assert "GOOGLE_OAUTH_REDIRECT_URI" in CLOUD_SECRET_NAMES


def test_local_environment_can_run_without_a_secrets_file():
    class MissingSecrets(dict):
        def get(self, key, default=None):
            raise FileNotFoundError("no local secrets file")

    environment = {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "publishable",
    }
    configure_streamlit_secrets(MissingSecrets(), environment)
