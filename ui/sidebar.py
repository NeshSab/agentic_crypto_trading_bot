"""
Sidebar interface components for application configuration and controls.

This module provides the sidebar user interface for the market intelligence
application, including API key management, model configuration, knowledge
base management, conversation export utilities, and session controls.

The sidebar serves as the primary configuration hub for users to set up
their environment, manage data sources, and control application behavior.
It integrates with multiple services and provides comprehensive controls
for the application's functionality.
"""

import os
import traceback
import streamlit as st
from datetime import datetime
from utils import format_duration, get_knowledge_base_files, get_personas_list
from widgets.exports import (
    export_conversation_json,
    export_conversation_csv,
    export_conversation_pdf,
)
from state import ui_session_state
from events import reset_session
from dotenv import load_dotenv

from ai.rag.rag_store import (
    build_faiss_from_documents,
    add_uploaded_files_to_index,
    add_url_content_to_index,
)
from ai.tools.web_load import web_load

load_dotenv()
OPENAI_ENV = os.getenv("OPENAI_API_KEY", "")

DEFAULT_KB = get_knowledge_base_files(
    base_patterns=[
        "../storage/knowledge_base/playbooks/*.md",
    ]
)


PERSONAS_LIST = get_personas_list()


def render_sidebar(index_path: str) -> None:
    ui_state = ui_session_state()

    st.markdown("# Settings")
    try:
        ui_state.api_key = OPENAI_ENV
        if not ui_state.api_key:
            st.error("OpenAI API key is required.")

        os.environ["OPENAI_API_KEY"] = ui_state.api_key
        ui_state.api_key_set = True

        os.makedirs("../storage/knowledge_base/var", exist_ok=True)
        if not os.path.exists(index_path):
            print("Building FAISS index from default KB...")
            build_faiss_from_documents(DEFAULT_KB, index_path)
    except Exception as e:
        st.error(f"Initialization failed: {e}")
        traceback.print_exc()

    if ui_state.api_key_set:
        st.subheader("AI Persona")
        ui_state.ai_persona = st.selectbox(
            "Select Persona",
            PERSONAS_LIST,
            index=(
                PERSONAS_LIST.index(ui_state.ai_persona)
                if ui_state.ai_persona in PERSONAS_LIST
                else 0
            ),
            help="Select the AI persona for this session",
        )

        with st.expander("Persona details", expanded=False):
            st.text(f"Current Persona: {ui_state.ai_persona}. ")
            st.text(
                f"With the creativity of {ui_state.temperature} (temperature),"
                f" response diversity of {ui_state.top_p} (top-p), "
                f"and a {ui_state.response_style} response style."
            )
            st.caption(
                "Parameters are bound to persona. If you wish to adjust, select "
                "and a new persona."
            )

        st.divider()

        st.subheader("Web Search")
        ui_state.enable_web_search = st.checkbox(
            "Enable Web Search",
            value=ui_state.enable_web_search,
            help="Allow AI to search approved financial news sources",
        )
        st.divider()

        st.subheader("📚 Knowledge Base (RAG)")
        st.caption(
            "Optionally add custom docs, e.g. financial quarterly report, "
            + "to the knowledge base."
        )

        uploaded = st.file_uploader(
            "Add docs (.md/.txt/.pdf)",
            type=["md", "txt", "pdf"],
            accept_multiple_files=True,
            key=f"file_uploader_{ui_state.file_uploader_key}",
        )
        if uploaded:
            st.info(f"📁 {len(uploaded)} document(s) uploaded and ready to process.")

            if st.button("Add to Knowledge Base", type="primary"):
                with st.spinner(f"Adding {len(uploaded)} document(s)..."):
                    try:
                        add_uploaded_files_to_index(uploaded, index_path)
                        st.success(f"✅ Added {len(uploaded)} document(s)!")

                        ui_state.file_uploader_key += 1
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Failed to add documents: {e}")

        st.markdown("**Or add content from URL:**")
        url_input = st.text_input(
            "Enter URL",
            placeholder="https://example.com/article",
            help="Add web content directly to knowledge base",
            key=f"web_uploader_{ui_state.web_uploader_key}",
        )

        if url_input.strip():
            if st.button("Add to Knowledge Base", type="secondary"):
                with st.spinner(f"Loading content from {url_input}..."):
                    try:
                        content = web_load.invoke({"link": url_input.strip()})
                        if content and content != "No content loaded":
                            add_url_content_to_index(
                                url_input.strip(), content, index_path
                            )
                            st.success("✅ Added content from URL to knowledge base!")
                        else:
                            st.error("❌ No content could be loaded from this URL")

                    except Exception as e:
                        st.error(f"❌ Failed to add URL content: {e}")

                    ui_state.web_uploader_key += 1
                    st.rerun()

        st.divider()

        with st.expander("💰 Usage & Cost (MOCKUP)", expanded=False):
            total_cost = 0
            st.metric("Total Session Cost", f"${total_cost:.4f}")
            now_ts = datetime.now().timestamp()
            session_secs = now_ts - float(ui_state.session_start_ts or now_ts)
            st.metric("Session Time", format_duration(session_secs))

            st.markdown("**Per Model Usage:**")
            model_usage = {}  # get_model_usage() if end up having usage tracking
            for model, usage in model_usage.items():
                tokens_in = usage["tokens_in"]
                tokens_out = usage["tokens_out"]
                cost = 1  # estimate_cost(model, tokens_in, tokens_out)

                with st.container():
                    st.markdown(f"**{model}**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("In", f"{tokens_in:,}")
                    with col2:
                        st.metric("Out", f"{tokens_out:,}")
                    col3, _ = st.columns(2)
                    with col3:
                        st.metric("Cost", f"${cost:.4f}")
            else:
                st.info("No usage data yet")

        st.divider()

        if (
            "ai_desk_messages" in st.session_state
            and len(st.session_state.ai_desk_messages) > 1
        ):
            st.subheader("📄 Export Conversation")
            export_format = st.selectbox(
                "Choose format:",
                ["JSON", "CSV", "PDF"],
                help="Export your conversation in different formats",
            )

            if st.button("Export Conversation", use_container_width=True):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"conversation_export_{timestamp}"
                    history = st.session_state.ai_desk_messages

                    if export_format == "JSON":
                        data = export_conversation_json(history)
                        st.download_button(
                            label="📥 Download JSON",
                            data=data,
                            file_name=f"{filename}.json",
                            mime="application/json",
                            use_container_width=True,
                        )
                    elif export_format == "CSV":
                        data = export_conversation_csv(history)
                        st.download_button(
                            label="📥 Download CSV",
                            data=data,
                            file_name=f"{filename}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )
                    elif export_format == "PDF":
                        data = export_conversation_pdf(history)
                        st.download_button(
                            label="📥 Download PDF",
                            data=data,
                            file_name=f"{filename}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    st.success(f"✅ {export_format} export ready for download!")
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")

            st.divider()

        if st.button("Reset session", type="primary", use_container_width=True):
            reset_session()
            st.rerun()
