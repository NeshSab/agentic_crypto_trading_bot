"""
Trade decision prompt template loader.

This module provides a function to generate an AI desk prompt using a Jinja2
template. It fills in details about the AI persona and current date context.
"""

from .template_loader import render_template
from datetime import datetime


def AI_DESK(
    ai_persona: dict,
) -> str:
    """
    Generate an AI desk prompt using Jinja2 template.

    Parameters
    ----------
    ai_persona: The AI persona/character dictionary containing all persona details

    Returns:
        Rendered prompt string
    """
    todays_date = datetime.utcnow().strftime("%Y-%m-%d")
    day_of_week = datetime.utcnow().strftime("%A")
    month = int(todays_date.split("-")[1])
    quarter = f"Q{(month-1)//3 + 1}"
    year = todays_date.split("-")[0]

    return render_template(
        "ai_desk.j2",
        ai_persona=ai_persona,
        todays_date=todays_date,
        day_of_week=day_of_week,
        quarter=quarter,
        year=year,
    )
