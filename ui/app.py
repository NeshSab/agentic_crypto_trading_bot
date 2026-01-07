"""
Main application file for the Crypto Market Intelligence Companion
and Trading Assistant.

This module sets up the Streamlit application, including page
configuration, logging, sidebar rendering, and tab management.
It integrates various components such as AI-driven analysis,
trading configurations, and informational content to provide a
comprehensive user experience.
"""

import logging
import streamlit as st
import os

os.environ["USER_AGENT"] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
    "Safari/537.36"
)

from state import init_state
from sidebar import render_sidebar
from tabs import about, trading_configs, ai_desk, trades_analysis


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LOGS_DIR = os.path.join(PROJECT_ROOT, "storage", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOGS_DIR, "app.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    force=True,
)
logging.info("Test log: Logging setup complete.")

TAB_RENDERERS = {
    "About": about.render,
    "Trading Configs": trading_configs.render,
    "AI Desk": ai_desk.render,
    "Trades Analysis": trades_analysis.render,
}
TABS = ["About", "Trading Configs", "Trades Analysis", "AI Desk"]
INDEX_PATH = os.path.join(
    PROJECT_ROOT, "storage", "knowledge_base", "var", "faiss_index"
)


st.set_page_config(
    page_title="Crypto Market Intelligence Companion",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()

with st.sidebar:
    render_sidebar(INDEX_PATH)


st.title("Crypto Market Intelligence Companion")

st.html(
    """
<style>
.stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { font-size: 18px; }
</style>
"""
)

tab_objs = st.tabs(TABS)


for tab, name in zip(tab_objs, TABS):
    with tab:
        TAB_RENDERERS[name]()
