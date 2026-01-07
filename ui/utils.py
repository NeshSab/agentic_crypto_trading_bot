"""
Utility functions for the UI components.

This module provides helper functions for formatting durations,
retrieving knowledge base files, and extracting persona information.
"""

import glob
import os
import json


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PERSONAS_DICTIONARY_PATH = os.path.join(
    PROJECT_ROOT, "storage", "configs", "personas.json"
)


def format_duration(seconds: float) -> str:
    """Format duration from seconds to 'Xh Ym Zs'."""
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def get_knowledge_base_files(base_patterns: list[str]) -> list[str]:
    """Get relevant markdown files for RAG indexing."""
    files = []
    for pattern in base_patterns:
        files.extend(glob.glob(pattern))

    return [f for f in files if os.path.exists(f)]


def get_personas_list() -> list[str]:
    """Extract list of persona names from personas data."""
    with open(PERSONAS_DICTIONARY_PATH, "r") as f:
        personas_data = json.load(f)

    return [persona["name"] for persona in personas_data.get("personas", [])]
