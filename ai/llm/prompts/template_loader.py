"""
Jinja2 template loader for AI prompts.

This module sets up the Jinja2 environment to load and render templates
used for generating AI prompts across the application.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
)


def load_template(template_name: str) -> str:
    """Load and return a Jinja2 template."""
    template = env.get_template(template_name)
    return template


def render_template(template_name: str, **kwargs) -> str:
    """Load and render a template with provided variables."""
    template = load_template(template_name)
    return template.render(**kwargs)
