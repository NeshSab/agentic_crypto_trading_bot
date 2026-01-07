"""
Message trimming middleware for managing conversation context windows.


"""

from langchain.agents.middleware import before_model
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.agents import AgentState
from langgraph.runtime import Runtime
from typing import Any


@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last 6 messages plus the first message to manage context window."""
    messages = state["messages"]

    if len(messages) <= 8:
        return None

    first_msg = messages[0]
    recent_messages = messages[-7:]

    new_messages = [first_msg] + recent_messages

    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]}
