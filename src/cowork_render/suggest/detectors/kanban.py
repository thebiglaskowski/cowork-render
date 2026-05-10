"""Kanban shape detector — H2 status columns + H3 cards."""

from __future__ import annotations

import re
from pathlib import Path

COLUMN_KEYWORDS = {
    "backlog", "to do", "todo", "in progress", "doing",
    "done", "complete", "completed", "blocked", "on hold",
    "review", "needs review",
}

_H2 = re.compile(r"^## (.+)$", re.MULTILINE)
_H3 = re.compile(r"^### .+$", re.MULTILINE)
_TRAILING_PAREN = re.compile(r"\s*\([^)]*\)\s*$")


def _normalise(title: str) -> str:
    return _TRAILING_PAREN.sub("", title).strip().lower()


def detect(content: str, source_path: Path) -> tuple[str, str, dict] | None:
    """Return (confidence, rationale, render_html_options) or None."""
    h2_titles = [m.group(1).strip() for m in _H2.finditer(content)]
    if not h2_titles:
        return None

    h3_count = len(_H3.findall(content))
    keyword_cols = [t for t in h2_titles if _normalise(t) in COLUMN_KEYWORDS]

    if len(keyword_cols) >= 2 and h3_count >= 1:
        kw_str = ", ".join(keyword_cols[:3])
        return (
            "high",
            f"{len(keyword_cols)} status columns ({kw_str}) with {h3_count} H3 cards",
            {"title": source_path.stem},
        )

    if (len(keyword_cols) >= 1 or len(h2_titles) >= 2) and h3_count >= 1:
        return (
            "medium",
            f"{len(h2_titles)} H2 columns with {h3_count} H3 cards",
            {"title": source_path.stem},
        )

    return None
