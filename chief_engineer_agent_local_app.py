"""Loopback-only Chief Engineer Agent UI backed by the local Qwen model."""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"
for import_root in (PROJECT_ROOT, SOURCE_ROOT):
    normalized = str(import_root.resolve())
    if normalized not in sys.path:
        sys.path.insert(0, normalized)

# This standalone entry point is intentionally local-first and does not read
# Ollama Cloud credentials or the full Teacher Portal's Supabase secrets.
os.environ["SYSTEM_ADMIN_AI_ENABLED"] = "true"
os.environ["MATH_TEACHER_AI_PROVIDER"] = "ollama"
os.environ["MATH_TEACHER_AI_MODEL"] = "qwen3:0.6b"
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:11434"
os.environ.pop("OLLAMA_API_KEY", None)

import streamlit as st

from portal_v2.ui.admin_chief_engineer_agent_streamlit import (
    render_admin_chief_engineer_agent,
)


st.set_page_config(page_title="AI Agent — Qwen local", page_icon="🤖")
st.caption(
    "Chế độ cục bộ: chỉ truy cập trên máy này, dùng Ollama `qwen3:0.6b`; "
    "không cần API key Ollama Cloud."
)
render_admin_chief_engineer_agent(st, admin_actor="local-admin")
