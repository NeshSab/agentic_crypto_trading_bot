"""
Conversation export utilities for multiple output formats.

This module provides functionality to export conversation histories from
the Crypto Market Intelligence Companion into various formats including JSON, CSV,
and PDF. The exports include metadata, timestamps, and proper formatting
for archival and sharing purposes.

"""

import json
import csv
from io import StringIO, BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def export_conversation_json(history) -> str:
    """
    Export conversation history as structured JSON format.

    Parameters
    ----------
    history : list
        List of conversation message objects with type and content attributes

    Returns
    -------
    str
        JSON-formatted conversation export with metadata
    """
    export_data = {"export_timestamp": datetime.now().isoformat(), "conversation": []}

    for i, msg in enumerate(history):
        if hasattr(msg, "type") and hasattr(msg, "content"):
            role = "user" if msg.type == "human" else "assistant"
            export_data["conversation"].append(
                {
                    "message_id": i + 1,
                    "role": role,
                    "content": msg.content,
                    "timestamp": getattr(msg, "timestamp", None),
                }
            )

    return json.dumps(export_data, indent=2, ensure_ascii=False)


def export_conversation_csv(history) -> str:
    """
    Export conversation history as CSV.

    Parameters
    ----------
    history : list
        List of conversation message objects with type and content attributes

    Returns
    -------
    str
        CSV-formatted conversation export
    """
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Message ID", "Role", "Content", "Timestamp"])
    for i, msg in enumerate(history):
        if hasattr(msg, "type") and hasattr(msg, "content"):
            role = "User" if msg.type == "human" else "Assistant"
            timestamp = getattr(msg, "timestamp", datetime.now().isoformat())
            writer.writerow([i + 1, role, msg.content, timestamp])

    return output.getvalue()


def export_conversation_pdf(history) -> bytes:
    """Export conversation history as PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=30,
    )

    user_style = ParagraphStyle(
        "UserMessage",
        parent=styles["Normal"],
        fontSize=11,
        leftIndent=0,
        spaceAfter=12,
    )

    assistant_style = ParagraphStyle(
        "AssistantMessage",
        parent=styles["Normal"],
        fontSize=11,
        leftIndent=0,
        spaceAfter=12,
    )

    story = []

    story.append(Paragraph("Conversation Export", title_style))
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Generated: {export_time}", styles["Normal"]))
    story.append(Spacer(1, 20))

    for _, msg in enumerate(history):
        if hasattr(msg, "type") and hasattr(msg, "content"):
            if msg.type == "human":
                story.append(Paragraph("<b>User:</b>", user_style))
                story.append(Paragraph(msg.content, user_style))
            else:
                story.append(Paragraph("<b>Assistant:</b>", assistant_style))
                story.append(Paragraph(msg.content, assistant_style))
            story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
