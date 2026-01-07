"""
Trade decision prompt template loader.

This module provides a function to generate a trade decision prompt using a Jinja2
template. It fills in details about the AI persona.
"""

from .template_loader import render_template


def TRADE_DECISION(
    ai_persona: str,
) -> str:
    """
    Generate trade decision prompt using Jinja2 template.

    Parameters
    ----------
    ai_persona: The AI persona/character

    Returns:
        Rendered prompt string
    """
    return render_template(
        "trade_decision.j2",
        ai_persona=ai_persona,
    )
