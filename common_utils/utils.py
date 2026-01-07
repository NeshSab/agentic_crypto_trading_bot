"""
Utility functions for persona and symbol management.

Includes functions to retrieve persona details, available trading symbols,
and current UTC date.
"""

import json
import logging
from datetime import datetime

PERSONAS_DICTIONARY_PATH = "../storage/configs/personas.json"
AVAILABLE_SYMBOLS_PATH = "../storage/configs/available_pairs.json"


def get_personas_llm_details(persona_name: str) -> dict | None:
    """Get persona details by persona name."""
    with open(PERSONAS_DICTIONARY_PATH, "r") as f:
        personas_data = json.load(f)

    for persona in personas_data.get("personas", []):
        if persona["name"] == persona_name:
            return persona["llm_parameters"]

    logging.warning(f"Persona '{persona_name}' not found in personas data.")
    return {"temperature": 0.7, "top_p": 0.9, "response_style": "concise"}


def get_persona_by_name(persona_name: str) -> dict | None:
    """Get full persona object by persona name."""
    try:
        with open(PERSONAS_DICTIONARY_PATH, "r") as f:
            personas_data = json.load(f)

        for persona in personas_data.get("personas", []):
            if persona["name"] == persona_name:
                return persona

        logging.warning(f"Persona '{persona_name}' not found in personas data.")
        return None
    except Exception as e:
        logging.error(f"Error loading persona data: {e}")
        return None


def get_available_symbol_pairs() -> dict:
    """Load available trading symbol pairs from JSON file."""
    try:
        with open(AVAILABLE_SYMBOLS_PATH, "r") as f:
            symbols_data = json.load(f)
        return symbols_data
    except Exception as e:
        logging.error(f"Error loading available symbol pairs: {e}")
        return {}


def current_date_utc():
    """
    Returns the current date (UTC) in formas "YYYY-MM-DD HH:MM:SS".
    """
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
