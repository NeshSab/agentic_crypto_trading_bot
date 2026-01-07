"""
Web content loading tool for article and document retrieval.

This module provides functionality to load complete content from specific
URLs, complementing web search capabilities by retrieving full article
text and document content. It uses LangChain's WebBaseLoader to extract
clean, structured content from web pages.

The tool is designed for scenarios where specific URLs need content
extraction, such as following up on search results or loading referenced
articles for comprehensive analysis.

Key features:
- Full article content extraction
- Clean text parsing from web pages
- Error handling and logging
- Integration with LangChain document loaders
- Structured content output for analysis
"""

import logging
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import tool
from langchain_community.document_loaders import WebBaseLoader


class WebLoaderInput(BaseModel):
    link: str = Field(..., description="Single URL to load content from")

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )


@tool(args_schema=WebLoaderInput)
def web_load(link: str) -> str:
    """
    **CONTENT LOADER**: Load full article content from a specific URL.

    Use this when you have a specific URL and need the complete article text.
    Complements web_search when you need content from particular links.
    """
    try:
        loader = WebBaseLoader(link)
        documents = loader.load()
    except Exception as e:
        logging.error(f"Error loading content from {link}: {e}")

    logging.info(documents[0].page_content[:100] if documents else "No content loaded")
    return documents[0].page_content if documents else "No content loaded"
