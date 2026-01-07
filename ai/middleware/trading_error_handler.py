"""
Trading-specific error handling middleware for AI agents.

This middleware captures and manages errors related to trading operations,
such as missing data, API failures, and invalid trade signals. It ensures that
the AI agent can gracefully handle issues without crashing, providing fallback
responses or logging errors for further analysis.
"""

from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langchain.messages import AIMessage, ToolMessage
from langgraph.runtime import Runtime
from typing import Any, Dict
import logging


class TradingErrorHandlerMiddleware(AgentMiddleware):
    """
    Custom middleware for handling trading-specific errors and logging AI decisions.
    """

    def __init__(self, log_decisions: bool = True):
        super().__init__()
        self.log_decisions = log_decisions
        self.logger = logging.getLogger(__name__)

    @hook_config(can_jump_to=["end"])
    def before_model(
        self, state: AgentState, runtime: Runtime
    ) -> Dict[str, Any] | None:
        """Validate input and check for trading data completeness."""
        messages = state.get("messages", [])
        if not messages:
            self.logger.warning("No messages provided to trading agent")
            return {
                "messages": [AIMessage("Error: No trading signal context provided")],
                "jump_to": "end",
            }
        if self.log_decisions:
            user_message = messages[-1].content if messages else "No content"
            self.logger.info(f"Processing trading signal: {user_message[:200]}...")

        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> Dict[str, Any] | None:
        """Log AI trade decisions and validate output."""
        if self.log_decisions and state.get("messages"):
            last_message = state["messages"][-1]
            if hasattr(last_message, "content"):
                self.logger.info(
                    f"AI trade decision generated: {last_message.content[:100]}..."
                )
            if hasattr(state, "structured_response"):
                decision = state.get("structured_response")
                if decision:
                    self.logger.info(
                        f"Trade Decision: {decision.get('action', 'UNKNOWN')} "
                        f"for {decision.get('symbol_pair', 'UNKNOWN')} "
                        f"with {decision.get('confidence', 'UNKNOWN')} confidence"
                    )

        return None

    def wrap_tool_call(self, request, handler):
        """Add error handling for tool calls (market data, news, etc.)."""
        try:
            return handler(request)
        except Exception as e:
            self.logger.error(f"Tool call failed for {request.tool.name}: {str(e)}")
            return ToolMessage(
                content=f"Tool {request.tool.name} temporarily unavailable. "
                f"Proceeding with available data.",
                tool_call_id=request.tool_call_id,
            )
