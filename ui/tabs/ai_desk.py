"""
AI Desk tab interface for interactive market intelligence conversations.

This module provides the main conversational interface for the market
intelligence assistant, handling user interactions, message formatting,
and chat flow management with simple memory management.
"""

import streamlit as st
import re
from ai.ai_agent import chat
from ui.state import ui_session_state


def get_static_greeting() -> str:
    """Return a static greeting message for the AI desk."""
    return (
        "👋 **Welcome to the AI Desk!** \n\n"
        "I'm your cryptocurrency market intelligence assistant. I can help you with:\n"
        "- **Market Analysis**: Current trends, sentiment, and regime analysis\n"
        "- **Crypto Sectors**: Layer 1s, Layer 2s, DeFi, GameFi, AI tokens, and more\n"
        "- **Research**: News, fundamentals, on-chain metrics, and market structure\n"
        "- **Educational Content**: Explaining concepts and market dynamics\n\n"
        "Feel free to ask me anything about the crypto markets!"
    )


def format_llm_response(response: str, tools_used: list = None) -> str:
    """
    Format LLM response text for display in the chat interface.

    Parameters
    ----------
    response : str
        Raw LLM response text
    tools_used : list, optional
        List of tools used during response generation

    Returns
    -------
    str
        Formatted response text ready for display
    """
    response = response.replace("$", "\\$")
    response = re.sub(r"\*\*([^*]+)\*\*", r"**\1**", response)
    response = re.sub(r"  +", " ", response)

    if tools_used:
        tools_str = ", ".join(tools_used)
        response += f"\n\n---\n**Tools used:** {tools_str}"

    return response


def render() -> None:
    ui_state = ui_session_state()
    if not ui_state.api_key_set:
        st.info("Please set your API keys in the sidebar first.")
        return

    st.header("🤖 AI Desk")
    st.caption(
        "Your AI-powered cryptocurrency market intelligence assistant. "
        "Ask questions about market trends, sectors, and analysis."
    )

    if "ai_desk_messages" not in st.session_state:
        st.session_state.ai_desk_messages = [
            {"role": "assistant", "content": get_static_greeting(), "tools_used": []}
        ]

    transcript = st.container(height=500, border=True)
    with transcript:
        for message in st.session_state.ai_desk_messages:
            role = message["role"]
            content = message["content"]
            tools_used = message.get("tools_used", [])

            with st.chat_message(role):
                if role == "assistant":
                    cleaned_response = format_llm_response(content, tools_used)
                    st.markdown(cleaned_response)
                else:
                    st.markdown(content)

    user_text = st.chat_input("Type your query…")
    if user_text and user_text.strip():
        st.session_state.ai_desk_messages.append(
            {"role": "user", "content": user_text.strip()}
        )

        with st.spinner("Thinking..."):
            try:
                result = chat(
                    user_text.strip(),
                    ui_state.enable_web_search,
                    ui_state.ai_persona,
                )
                if isinstance(result, tuple):
                    response, tools_used = result
                else:
                    response = result
                    tools_used = []

                st.session_state.ai_desk_messages.append(
                    {"role": "assistant", "content": response, "tools_used": tools_used}
                )

            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.ai_desk_messages.append(
                    {"role": "assistant", "content": error_msg, "tools_used": []}
                )
                st.error(f"Error processing your request: {str(e)}")

        st.rerun()
