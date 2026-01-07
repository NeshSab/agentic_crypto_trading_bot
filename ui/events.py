"""
UI event handlers and session management utilities.

This module provides event handling functions for the Streamlit UI,
at this stage primarily focusing on session reset functionality.
"""

import streamlit as st
import logging


def reset_session() -> None:
    """
    Perform complete session reset and application restart.

    Clears all session state including API keys, settings, and
    user data. Forces application rerun to provide fresh start.
    """
    st.session_state.clear()
    logging.info("Session state cleared for complete reset.")
    st.rerun()
