"""
Trading configuration tab for the Crypto Market Intelligence Companion.

This module provides the user interface for configuring trading
parameters, including AI persona selection, technical indicator settings,
and symbol-specific configurations. Users can adjust these settings
to tailor the trading agent's behavior according to their preferences
and strategies.
"""

import streamlit as st
import pathlib
from state import ui_session_state
from data_access.configs import ConfigDataAccess
from utils import get_personas_list
from common_utils.utils import get_personas_llm_details, get_available_symbol_pairs


def render():
    ui_state = ui_session_state()
    st.subheader("Select Trading Agent Persona")
    personas = get_personas_list()
    bot_ai_persona = st.selectbox(
        "AI Persona",
        personas,
        index=(
            personas.index(ui_state.bot_ai_persona)
            if ui_state.bot_ai_persona in personas
            else 0
        ),
        help="Select the AI persona that will guide the trading decisions.",
    )
    with st.expander("Persona details", expanded=False):
        temperature, top_p, response_style = get_personas_llm_details(
            ui_state.bot_ai_persona
        ).values()
        st.text(
            f"Creativity of {temperature} (temperature),"
            f" response diversity of {top_p} (top-p), "
            f"and a {response_style} response style."
        )
        st.caption(
            "Parameters are bound to persona. If you wish to adjust, select "
            "and a new persona."
        )
    st.divider()

    st.subheader("Set Technical Indicator Parameters")
    fast_window = st.number_input(
        "Fast Window",
        min_value=1,
        max_value=100,
        value=ui_state.fast_window,
        step=1,
        help="Number of periods for the fast moving average.",
    )
    slow_window = st.number_input(
        "Slow Window",
        min_value=1,
        max_value=200,
        value=ui_state.slow_window,
        step=1,
        help="Number of periods for the slow moving average.",
    )
    confirmation_indicator_window = st.number_input(
        "Confirmation Indicator Window",
        min_value=1,
        max_value=100,
        value=ui_state.confirmation_indicator_window,
        step=1,
        help="Number of periods for the confirmation indicator.",
    )
    atr_window = st.number_input(
        "ATR Window",
        min_value=1,
        max_value=100,
        value=ui_state.atr_window,
        step=1,
        help="Number of periods for the ATR calculation.",
    )
    atr_multiplier = st.number_input(
        "ATR Multiplier",
        min_value=0.1,
        max_value=10.0,
        value=float(ui_state.atr_multiplier),
        step=0.1,
        format="%.2f",
        help="Multiplier for the ATR to set stop-loss levels.",
    )

    st.divider()
    st.subheader("Modify Symbol Configurations")
    symbol_configs = ui_state.symbol_configs
    if symbol_configs:
        st.markdown("Current Symbol Configurations")
        st.caption(
            "List of symbol pairs with their respective maximum allocation percentages."
        )
        for symbol_pair, max_allocation in symbol_configs.items():
            st.markdown(f"- **{symbol_pair}**: {max_allocation}")
        st.write("")
    else:
        st.info("No symbol configurations set yet.")

    available_symbols_dict = get_available_symbol_pairs()

    selected_symbol = st.radio(
        "Show available crypto",
        ["name", "symbol pair"],
        index=1,
        horizontal=True,
    )
    if selected_symbol == "name":
        symbol_options = list(available_symbols_dict.keys())
    else:
        symbol_options = list(available_symbols_dict.values())
    selected_symbol_pair = st.selectbox(
        "Select Symbol Pair to Configure",
        symbol_options,
    )
    if selected_symbol == "name":
        symbol_pair = available_symbols_dict[selected_symbol_pair]
    else:
        symbol_pair = selected_symbol_pair
    max_allocation = st.number_input(
        "Max Allocation (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(ui_state.symbol_configs.get(symbol_pair, 0.0)),
        step=0.1,
        help="Maximum allocation percentage for the selected symbol pair.",
    )
    if symbol_pair in symbol_configs:
        col1, col2 = st.columns(spec=[1, 8], gap="small")
        with col1:
            if st.button("Update"):
                symbol_configs[symbol_pair] = round(max_allocation, 1)
                st.success(f"Updated configuration for {symbol_pair}.")
                st.rerun()
        with col2:
            if st.button("Remove"):
                symbol_configs.pop(symbol_pair)
                st.success(f"Removed configuration for {symbol_pair}.")
                st.rerun()
    else:
        if st.button("Add"):
            symbol_configs[symbol_pair] = round(max_allocation, 1)
            st.success(f"Added configuration for {symbol_pair}.")
            st.rerun()

    st.divider()
    if st.button("Save Trading Configurations"):
        ui_state.bot_ai_persona = bot_ai_persona
        ui_state.fast_window = fast_window
        ui_state.slow_window = slow_window
        ui_state.confirmation_indicator_window = confirmation_indicator_window
        ui_state.atr_window = atr_window
        ui_state.atr_multiplier = atr_multiplier
        ui_state.symbol_configs = symbol_configs

        db_path = str(
            pathlib.Path(__file__).parent.parent.parent / "storage" / "trading.db"
        )
        config_obj = ConfigDataAccess(db_path)
        config_obj.connect()

        new_user_config_params = {
            "ai_persona": bot_ai_persona,
            "fast_window": fast_window,
            "slow_window": slow_window,
            "confirmation_indicator_window": confirmation_indicator_window,
            "atr_window": atr_window,
            "atr_multiplier": atr_multiplier,
            "date_added": None,
        }

        previous_config = config_obj.get_current_configs()
        if previous_config:
            (
                id,
                _ai_persona,
                _fast_window,
                _slow_window,
                _confirmation_indicator_window,
                _atr_window,
                _atr_multiplier,
                _usage,
                _added_at,
                _discontinued_at,
            ) = previous_config
            config_obj.update_discontinued_config_by_id(id, {"discontinued_date": None})
        config_obj.set_new_config_as_current(new_user_config_params)

        previous_symbol_configs_table = config_obj.get_current_active_symbol_configs()
        if previous_symbol_configs_table:
            for symbol_config in previous_symbol_configs_table:
                (
                    id,
                    symbol_pair,
                    max_allocation,
                    _usage,
                    _added_at,
                    _discontinued_at,
                ) = symbol_config
                config_obj.update_discontinued_symbol_config_by_id(
                    id, {"discontinued_date": None}
                )

        for symbol_pair, max_allocation in symbol_configs.items():
            symbol_config_params = {
                "symbol_pair": symbol_pair,
                "max_allocation": max_allocation,
                "date_added": None,
            }
            config_obj.set_new_symbol_config_as_current(symbol_config_params)

        config_obj.close()
        st.success("Trading configuration updated in session.")
