"""
UI session state management using Pydantic.

This module defines the Session class to manage UI state with type
consistency and provides functions to initialize and retrieve the session state.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
import streamlit as st
import logging
from pydantic import BaseModel, Field
import pathlib

from common_utils.utils import get_personas_llm_details
from data_access.configs import ConfigDataAccess


class Session(BaseModel):
    """Session state using Pydantic for consistency."""

    ai_persona: str = "Sherlock Holmes"
    response_style: str = "Concise"
    temperature: float = 0.7
    top_p: float = 0.9

    bot_ai_persona: str = "Sherlock Holmes"
    fast_window: int = 9
    slow_window: int = 21
    confirmation_indicator_window: int = 10
    atr_window: int = 14
    atr_multiplier: float = 1.7

    symbol_configs: dict = {
        "BTC-EUR": 40.0,
        "ETH-EUR": 30.0,
        "XRP-EUR": 30.0,
        "LTC-EUR": 15.0,
        "SOL-EUR": 20.0,
        "BNB-EUR": 10.0,
        "ADA-EUR": 10.0,
    }

    api_key: str = ""
    api_key_set: bool = False

    tokens_in: int = 0
    tokens_out: int = 0

    enable_web_search: bool = False
    file_uploader_key: int = 0
    web_uploader_key: int = 0

    session_start_ts: float = Field(default_factory=lambda: datetime.now().timestamp())
    ai_desk_messages: list = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


def init_state() -> None:
    """Initialize session state on first run."""
    if "ui_session_state" not in st.session_state:
        try:
            db_path = str(
                pathlib.Path(__file__).parent.parent / "storage" / "trading.db"
            )
            config_obj = ConfigDataAccess(db_path)
            config_obj.connect()
            db_config = config_obj.get_current_configs()
            symbol_configs_table = config_obj.get_current_active_symbol_configs()
            symbol_configs = {}
            for symbol_config in symbol_configs_table:
                (
                    _id,
                    symbol_pair,
                    max_allocation,
                    _usage,
                    _added_at,
                    _discontinued_at,
                ) = symbol_config
                symbol_configs[symbol_pair] = max_allocation

            config_obj.close()
            print(f"Loaded user config from DB.{db_config}")
        except Exception as e:
            logging.warning(f"Could not load user config from DB: {e}")
            db_config = None
            symbol_configs = {}
        session = Session()
        if db_config:
            (
                _id,
                ai_persona,
                fast_window,
                slow_window,
                confirmation_indicator_window,
                atr_window,
                atr_multiplier,
                _usage,
                _added_at,
                _discontinued_at,
            ) = db_config
            temperature, top_p, response_style = get_personas_llm_details(
                ai_persona
            ).values()
            session.ai_persona = ai_persona
            session.bot_ai_persona = ai_persona
            session.response_style = response_style
            session.temperature = temperature
            session.top_p = top_p
            session.fast_window = fast_window
            session.slow_window = slow_window
            session.confirmation_indicator_window = confirmation_indicator_window
            session.atr_window = atr_window
            session.atr_multiplier = atr_multiplier
        if symbol_configs:
            session.symbol_configs = symbol_configs
            print(f"Loaded symbol configs from DB: {symbol_configs}")
        st.session_state.ui_session_state = session
        logging.info("Initialized new UI session state.")


def ui_session_state() -> Session:
    """
    Return the UI session state object.
    """
    if "ui_session_state" not in st.session_state:
        init_state()
    return st.session_state.ui_session_state
