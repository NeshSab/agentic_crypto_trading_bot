"""Central registry for all tools in LangChain @tool format."""

from .web_search import web_search
from .wikipedia_load import search_wikipedia
from .rag_search import search_knowledge_base
from .web_load import web_load
from .crypto_regime import analyze_crypto_regime
from .crypto_fundamentals import analyze_crypto_fundamentals
from .crypto_combined_analysis import analyze_crypto_combined


def get_trade_tools(enable_web_search: bool = False, rag_search: bool = False) -> list:
    """
    Return tool list for LangChain function calling.

    Parameters
    ----------
    enable_web_search : bool, default False
        Whether to include web search tool in the registry

    Returns
    -------
    list
        List of LangChain tool functions
    """
    available_tools = [
        # analyze_crypto_regime,
        # analyze_crypto_fundamentals,
        analyze_crypto_combined,
    ]

    if enable_web_search:
        available_tools.append(web_search)

    if rag_search:
        available_tools.append(search_knowledge_base)

    return available_tools


def get_research_tools(enable_web_search: bool = False) -> list:
    """
    Return research-focused tool list for the AI Desk agent.

    Parameters
    ----------
    enable_web_search : bool, default True
        Whether to include web search tool in the registry

    Returns
    -------
    list
        List of LangChain tool functions optimized for research
    """
    available_tools = [
        search_knowledge_base,
        search_wikipedia,
        web_load,
        analyze_crypto_regime,
        analyze_crypto_fundamentals,
    ]

    if enable_web_search:
        available_tools.append(web_search)

    return available_tools
