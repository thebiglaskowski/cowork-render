"""Timeline shape detector — H2–H4 headings with YYYY-MM-DD — title prefix."""

from __future__ import annotations

import re
from pathlib import Path

_DATE_HEADING = re.compile(
    r"^(?P<level>#{2,4})\s+\d{4}-\d{2}-\d{2}\s+—\s+.+$",
    re.MULTILINE,
)


def detect(content: str, source_path: Path) -> tuple[str, str, dict] | None:
    """Return (confidence, rationale, render_html_options) or None."""
    matches = list(_DATE_HEADING.finditer(content))
    if not matches:
        return None

    levels = [len(m.group("level")) for m in matches]
    entry_level = max(set(levels), key=levels.count)
    level_matches = [m for m in matches if len(m.group("level")) == entry_level]
    count = len(level_matches)

    options = {"title": source_path.stem, "entry_heading_level": entry_level}

    if count >= 3:
        return (
            "high",
            f"{count} date-prefixed H{entry_level} headings",
            options,
        )
    if count >= 2:
        return (
            "medium",
            f"{count} date-prefixed H{entry_level} headings",
            options,
        )
    return None
