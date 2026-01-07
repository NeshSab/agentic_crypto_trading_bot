"""
Wikipedia content search and retrieval tool for reference information.

This module provides Wikipedia search capabilities for background information,
context, and reference material to supplement market analysis and research.
It serves as a reliable source for company information, economic concepts,
and historical context.

The tool is designed to provide additional context after primary knowledge
base searches, offering comprehensive background information from Wikipedia's
extensive database of articles and references.

Key features:
- Wikipedia article search and retrieval
- Multiple article summary extraction
- Company and economic concept research
- Historical context and background information
- Reference material for comprehensive analysis
"""

import logging
import wikipedia
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import tool


class WikipediaSearchInput(BaseModel):
    query: str = Field(..., description="The search query for Wikipedia")

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )


@tool(args_schema=WikipediaSearchInput)
def search_wikipedia(query: str) -> str:
    """
    **REFERENCE SOURCE**: Search Wikipedia for background information and context.

    Use this for:
    • Company background, history, and business model information
    • Economic concepts, financial terms, and definitions
    • Historical events that impact markets
    • General knowledge to provide context for analysis

    Use after knowledge base search for additional context.
    """
    page_titles = wikipedia.search(query)
    titles = []
    summaries = []
    sources = []

    for page_title in page_titles[:3]:
        try:
            wiki_page = wikipedia.page(title=page_title, auto_suggest=False)
            titles.append(page_title)
            summaries.append(f"Summary: {wiki_page.summary}")
            sources.append(f"{page_title}: {wiki_page.url}")
        except (
            wikipedia.exceptions.PageError,
            wikipedia.exceptions.DisambiguationError,
        ):
            pass

    if not summaries:
        return "No good Wikipedia Search Result was found"

    result = ""
    for title, summary in zip(titles, summaries):
        result += f"\n\n*Page: {title}*"
        result += f"\n{summary}"

    if sources:
        result += f"\n\n*Wikipedia Sources: {', '.join(sources)}*"
    logging.info(result[:100])
    return result
