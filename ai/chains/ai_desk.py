"""
AI Desk research agent builder.

This module provides a function to build an AI Desk research agent using LangChain.
"""

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ToolRetryMiddleware,
    ModelRetryMiddleware,
)
from langgraph.checkpoint.memory import InMemorySaver

from ai.middleware.trading_error_handler import TradingErrorHandlerMiddleware
from ai.middleware.message_trimmer import trim_messages
from ai.middleware.input_sanitizer import (
    create_input_sanitizer_middleware_class,
)
from ai.llm.prompts.ai_desk import AI_DESK
from ai.tools.registry import get_research_tools

import traceback


def build_ai_desk_agent(
    *,
    llm,
    ai_persona: dict,
    enable_web_search: bool,
    enable_middleware: bool = True,
):
    """
    Builds the AI desk research agent with persistent memory and message trimming.

    This agent:
    - provides cryptocurrency market research and analysis
    - uses tools for market data, news, regime analysis, etc.
    - responds in natural language aligned with persona style
    - includes persistent conversation memory with automatic trimming
    - includes error handling and retry logic for reliability
    """
    print("Building AI Desk agent...")
    system_prompt = AI_DESK(ai_persona=ai_persona)
    print("System prompt for AI Desk agent created.")
    tools = get_research_tools(enable_web_search)
    print(f"Registered {len(tools)} tools for AI Desk agent.")
    middleware = []
    if enable_middleware:
        input_sanitizer = create_input_sanitizer_middleware_class(
            max_input_length=5000,
            enable_prompt_injection_detection=True,
            enable_content_moderation=True,
            enable_html_sanitization=True,
            strict_mode=False,
        )
        middleware = [
            input_sanitizer,
            trim_messages,
            ToolRetryMiddleware(
                max_retries=3,
                backoff_factor=1.5,
                initial_delay=0.5,
                retry_on=(ConnectionError, TimeoutError),
                on_failure="return_message",
            ),
            ModelRetryMiddleware(
                max_retries=2,
                backoff_factor=1.5,
                initial_delay=0.5,
                retry_on=(ConnectionError, TimeoutError),
            ),
            TradingErrorHandlerMiddleware(log_decisions=False),
        ]
    print("Middleware for AI Desk agent set up.")
    try:
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            middleware=middleware,
            checkpointer=InMemorySaver(),
        )
    except Exception as e:
        print(f"Error creating AI Desk agent: {e}")
        traceback.print_exc()
    print("AI Desk agent created successfully.")
    return agent
