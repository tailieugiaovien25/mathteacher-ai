"""Streamlit Community Cloud entry point for MathTeacher-AI."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping, MutableMapping


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"
CLOUD_SECRET_NAMES = (
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "GOOGLE_OAUTH_CLIENT_ID",
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "GOOGLE_OAUTH_REDIRECT_URI",
)


def configure_python_path(
    project_root: Path = PROJECT_ROOT,
    source_root: Path = SOURCE_ROOT,
    search_path: list[str] | None = None,
) -> list[str]:
    """Make repository packages importable without a local PYTHONPATH."""
    target = sys.path if search_path is None else search_path
    for path in (project_root, source_root):
        normalized = str(path.resolve())
        if normalized not in target:
            target.insert(0, normalized)
    return target


def copy_secrets_to_environment(
    secrets: Mapping[str, object],
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Expose only known app settings to existing environment-based adapters."""
    target = os.environ if environment is None else environment
    for name in CLOUD_SECRET_NAMES:
        value = str(secrets.get(name, "")).strip()
        if value and not target.get(name):
            target[name] = value


def configure_streamlit_secrets(
    secrets: Mapping[str, object],
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Allow local environment-only runs while requiring cloud configuration."""
    target = os.environ if environment is None else environment
    try:
        copy_secrets_to_environment(secrets, target)
    except Exception:
        if not target.get("SUPABASE_URL") or not target.get(
            "SUPABASE_PUBLISHABLE_KEY"
        ):
            raise


def run() -> None:
    configure_python_path()
    import streamlit as st

    configure_streamlit_secrets(st.secrets)
    from scripts.teacher_portal.app import main

    main()


if __name__ == "__main__":
    run()
