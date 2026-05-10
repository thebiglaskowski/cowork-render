"""Shared inline-markdown renderer used by kanban and timeline renderers."""

from __future__ import annotations

import html
import re


def render_inline_markdown(body: str) -> str:
    """Render inline markdown as HTML paragraphs, HTML-escaping first.

    Applies bold, italic, inline-code, and link transforms in that order,
    then wraps each blank-line-separated paragraph in <p> tags.
    """
    escaped = html.escape(body)
    parts = []
    for para in re.split(r"\n\n+", escaped):
        text = para.strip()
        if not text:
            continue
        text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(\S[^*]*?\S|\S)\*', r'<em>\1</em>', text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        parts.append(f"<p>{text}</p>")
    return "".join(parts)
