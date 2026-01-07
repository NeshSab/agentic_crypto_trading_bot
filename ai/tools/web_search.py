"""
Web search tool for financial news and market information retrieval.

This module provides web search capabilities using DuckDuckGo search engine
with filtering to approved financial news sources. It ensures reliable,
credible information sources for market analysis and research.

The tool integrates with LangChain's tool framework and provides structured
search results filtered by domain allowlists to maintain information quality
and relevance for financial analysis workflows.

Key features:
- DuckDuckGo search integration
- Approved financial domain filtering
- Structured search result formatting
- Market information focused queries
- Quality source validation
"""

import json
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults


class WebSearchInput(BaseModel):
    query: str = Field(
        ..., description="Search query for financial news and market information"
    )

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )


def load_approved_domains(
    path: str = "../storage/configs/approved_domains.json",
) -> list[str]:
    """Load approved domains from JSON config file."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data.get("domains", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"Could not load approved domains: {e}")
        return []


def filter_results_by_domain(
    results: list[dict], allowed_domains: list[str]
) -> list[dict]:
    """Filter search results to only include approved domains."""
    if not allowed_domains or not results:
        return results if results else []

    filtered_results = []

    for result in results:
        if isinstance(result, dict) and "link" in result:
            link = result.get("link", "").lower()
            domain_matches = any(domain.lower() in link for domain in allowed_domains)
            if domain_matches:
                filtered_results.append(result)

    return filtered_results


@tool(args_schema=WebSearchInput)
def web_search(query: str) -> str:
    """
    **REAL-TIME NEWS**: Search for the most recent financial news from trusted sources.

    Use this for:
    • Latest market developments and breaking financial news
    • Recent company earnings reports and announcements
    • Current economic data releases and central bank updates
    • Today's sector trends and market movements

    Returns up to 5 most recent articles from approved financial sources.
    """
    try:
        search = DuckDuckGoSearchResults(
            backend="news", output_format="list", num_results=10
        )
        results = search.invoke(query)

        allowed_domains = load_approved_domains()
        filtered_results = filter_results_by_domain(results, allowed_domains)

        if not filtered_results:
            return "No recent financial news found from approved sources."

        filtered_results.sort(key=lambda x: x.get("date", ""), reverse=True)
        if len(filtered_results) > 3:
            filtered_results = filtered_results[:3]

        formatted_results = []
        for i, result in enumerate(filtered_results, 1):
            title = result.get("title", "No title")
            snippet = result.get("snippet", "No snippet")
            link = result.get("link", "No link")
            source = result.get("source", "Unknown source")
            date = result.get("date", "No date")

            formatted_result = (
                f"{i}. **{title}**\n"
                f"   Source: {source} | Date: {date}\n"
                f"   {snippet}\n"
                f"   Link: {link}\n"
            )
            formatted_results.append(formatted_result)

        result_count = len(filtered_results)
        header = f"Found {result_count} recent financial news articles:\n\n"

        logging.info((header + "\n".join(formatted_results))[:100])
        return header + "\n".join(formatted_results)

    except Exception as e:
        logging.error(f"Error performing web search: {e}")
        return f"Error performing web search: {str(e)}"
