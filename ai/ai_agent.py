"""
AI agent module for evaluating trading signals and providing insights.

This module defines functions to evaluate trading signals using an AI agent
and to facilitate chat interactions for market research. It leverages
language models and predefined personas to generate trade evaluations and
responses.
"""

import json
import logging
from ai.chains.trade_advisor import build_trade_advisor_agent
from ai.chains.ai_desk import build_ai_desk_agent
from ai.llm.openai_client import OpenAIClient
from langchain_core.rate_limiters import InMemoryRateLimiter
from .storage.db_access import DatabaseAccess

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common_utils.utils import get_persona_by_name


RATE_LIMITER = InMemoryRateLimiter(
    requests_per_second=2,
    check_every_n_seconds=0.1,
    max_bucket_size=5,
)
LLM_CLIENT = OpenAIClient(rate_limiter=RATE_LIMITER)
DB_ACCESS = DatabaseAccess("../storage/trading.db")


def evaluate_trade(signal_context: dict, signal_id: int) -> dict:
    """
    Evaluate a trading signal using the AI agent with error handling and retry logic.

    Parameters
    ----------
        signal_context: Dictionary containing trading signal data

    Returns:
        Dictionary containing the structured trade decision
    """
    try:
        DB_ACCESS.connect()
        ai_persona_name = DB_ACCESS.get_current_ai_persona()
        DB_ACCESS.close()
    except Exception as e:
        logging.error(f"Database access failed: {e}")
        return None, None

    try:
        ai_persona = get_persona_by_name(ai_persona_name)
        if not ai_persona:
            logging.error(f"Persona '{ai_persona_name}' not found")
            return None, None

        persona_llm_config = ai_persona["llm_parameters"]
        settings = {
            "temperature": persona_llm_config["temperature"],
            "top_p": persona_llm_config["top_p"],
        }
    except Exception as e:
        logging.error(f"Failed to get persona config: {e}")
        return None, None

    try:
        llm = LLM_CLIENT.get_llm(settings)

        trade_advisor_agent = build_trade_advisor_agent(
            llm=llm,
            ai_persona=ai_persona,
            enable_middleware=True,
        )

        logging.info("[DEBUG] Trade advisor agent created successfully")

        result = trade_advisor_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": json.dumps(signal_context, indent=2),
                    }
                ]
            },
            config={"tags": ["bot", "trade_advisor"]},
        )

        tools_used = []
        if "messages" in result:
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tools_used.extend(
                        [
                            tool_call.get("name", "unknown_tool")
                            for tool_call in msg.tool_calls
                        ]
                    )
                elif (
                    hasattr(msg, "additional_kwargs")
                    and "tool_calls" in msg.additional_kwargs
                ):
                    tools_used.extend(
                        [
                            tool_call.get("function", {}).get("name", "unknown_tool")
                            for tool_call in msg.additional_kwargs["tool_calls"]
                        ]
                    )
        logging.info(f"Tools used during evaluation: {tools_used}")

        if "structured_response" not in result:
            logging.warning("No structured response found in agent result")
            return None, None

        structured_response = result["structured_response"]

        if hasattr(structured_response, "model_dump"):
            response_dict = structured_response.model_dump()
        elif hasattr(structured_response, "dict"):
            response_dict = structured_response.dict()
        else:
            response_dict = structured_response

        logging.info(f"Trade evaluation result: {response_dict}")

        try:
            DB_ACCESS.connect()
            user_configs_id = DB_ACCESS.get_current_user_configs_id()

            key_factors_str = (
                str(response_dict.get("key_factors", ""))
                if response_dict.get("key_factors")
                else ""
            )

            params = {
                "signal_id": signal_id,
                "user_configs_id": user_configs_id,
                "symbol_pair": response_dict.get("symbol_pair"),
                "fast_timeframe": response_dict.get("fast_timeframe"),
                "slow_timeframe": response_dict.get("slow_timeframe"),
                "strategy": response_dict.get("strategy"),
                "signal": response_dict.get("signal"),
                "action": response_dict.get("action"),
                "confidence": response_dict.get("confidence"),
                "risk_score": response_dict.get("risk_score"),
                "position_size_pct": response_dict.get("position_size_pct"),
                "stop_loss_pct": response_dict.get("stop_loss_pct"),
                "take_profit_pct": response_dict.get("take_profit_pct"),
                "rationale": response_dict.get("rationale"),
                "key_factors": key_factors_str,
                "source": "AI Trade Advisor Agent",
                "model_name": llm.model_name,
                "tools_used": ", ".join(tools_used),
            }
            DB_ACCESS.log_ai_decision(params)
            DB_ACCESS.close()
        except Exception as e:
            logging.error(f"Failed to log AI decision: {e}")

        return response_dict.get("action"), response_dict.get("position_size_pct")

    except Exception as e:
        logging.error(f"Trade evaluation failed: {e}")
        return None, None


def chat(user_query: str, enable_web_search: bool, ai_persona_name: str) -> str:
    """
    Chat with the AI desk agent for cryptocurrency market research and analysis.

    Parameters
    ----------
        user_query: User's question or request for market analysis
        enable_web_search: Boolean flag to enable web search tools
        ai_persona_name: Name of the AI persona to use for the agent

    Returns:
        String containing the AI desk agent's response
    """

    try:
        ai_persona = get_persona_by_name(ai_persona_name)
        if not ai_persona:
            logging.error(f"Persona '{ai_persona_name}' not found")
            return (
                "Sorry, I'm experiencing technical difficulties with "
                + "my persona configuration.",
            ), []

        persona_llm_config = ai_persona["llm_parameters"]
        settings = {
            "temperature": persona_llm_config["temperature"],
            "top_p": persona_llm_config["top_p"],
        }
    except Exception as e:
        logging.error(f"Failed to get persona config: {e}")
        return (
            "Sorry, I'm experiencing technical difficulties with my configuration.",
        ), []

    try:
        llm = LLM_CLIENT.get_llm(settings)
        ai_desk_agent = build_ai_desk_agent(
            llm=llm,
            ai_persona=ai_persona,
            enable_web_search=enable_web_search,
            enable_middleware=True,
        )

        result = ai_desk_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_query,
                    }
                ]
            },
            config={
                "configurable": {"thread_id": "ai_desk_thread"},
                "tags": ["ui", "ai_desk"],
            },
        )

        logging.info(f"AI Desk Agent query: {user_query}")

        tools_used = []
        if "messages" in result:
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tools_used.extend(
                        [
                            tool_call.get("name", "unknown_tool")
                            for tool_call in msg.tool_calls
                        ]
                    )
                elif (
                    hasattr(msg, "additional_kwargs")
                    and "tool_calls" in msg.additional_kwargs
                ):
                    tools_used.extend(
                        [
                            tool_call.get("function", {}).get("name", "unknown_tool")
                            for tool_call in msg.additional_kwargs["tool_calls"]
                        ]
                    )

        logging.info(f"Tools used during research: {tools_used}")

        response_content = "Sorry, I couldn't generate a response."
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                response_content = last_message.content
        elif "output" in result:
            response_content = result["output"]

        return response_content, tools_used

    except Exception as e:
        logging.error(f"AI Desk chat failed: {e}")
        return (
            "Sorry, I encountered an error while processing your request. "
            + "Please try again."
        ), []
