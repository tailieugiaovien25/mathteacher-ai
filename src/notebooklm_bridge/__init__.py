"""NotebookLM source-pack bridge for personal NotebookLM accounts.

This module prepares source files for manual import into the consumer NotebookLM
website. It does not automate or impersonate NotebookLM's private web interface.
"""

from notebooklm_bridge.source_pack import (
    NotebookLMSourcePack,
    NotebookLMSourcePackError,
    build_notebooklm_source_pack,
)

__all__ = [
    "NotebookLMSourcePack",
    "NotebookLMSourcePackError",
    "build_notebooklm_source_pack",
]
