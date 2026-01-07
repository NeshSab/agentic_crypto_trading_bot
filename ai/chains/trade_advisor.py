"""
Trade advisor agent builder.

This module provides a function to build a trade advisor agent using LangChain.
"""

import logging
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import (
    ToolRetryMiddleware,
    ModelRetryMiddleware,
)

from ai.schemas.trade import TradeDecision
from ai.middleware.trading_error_handler import TradingErrorHandlerMiddleware
from ai.llm.prompts.trade_decision import TRADE_DECISION
from ai.tools.registry import get_trade_tools


def build_trade_advisor_agent(
    *,
    llm,
    ai_persona: dict,
    enable_middleware: bool = True,
):
    """
    Builds the trade advisor agent.

    This agent:
    - evaluates deterministic signals
    - optionally uses tools (news, funding, etc.)
    - returns a structured TradeDecision
    - includes error handling and retry logic for reliability
    """

    system_prompt = TRADE_DECISION(ai_persona=ai_persona)

    tools = get_trade_tools(enable_web_search=True)

    middleware = []
    if enable_middleware:
        middleware = [
            ToolRetryMiddleware(
                max_retries=2,
                backoff_factor=2.0,
                initial_delay=1.0,
                retry_on=(
                    ConnectionError,
                    TimeoutError,
                ),
                on_failure="return_message",
            ),
            ModelRetryMiddleware(
                max_retries=2,
                backoff_factor=1.5,
                initial_delay=0.5,
                retry_on=(
                    ConnectionError,
                    TimeoutError,
                ),
            ),
            TradingErrorHandlerMiddleware(log_decisions=True),
        ]
    logging.info(
        f"Trade advisor agent created with {len(tools)} tools "
        f"and middleware enabled: {enable_middleware}"
    )
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        response_format=ToolStrategy(TradeDecision),
        middleware=middleware,
    )
