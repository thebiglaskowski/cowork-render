"""Kanban shape detector — H2 status columns + H3 cards."""

from __future__ import annotations

import re
from pathlib import Path

COLUMN_KEYWORDS = {
    "now", "next", "later", "done", "cut", "skipped", "backlog",
    "in progress", "in-progress", "doing", "todo", "to-do",
    "blocked", "waiting", "review", "shipped", "completed",
    "this week", "this sprint", "queued", "parked", "deferred",
    "active", "pending", "on hold", "on-hold",
}

_H2 = re.compile(r"^## (.+)$", re.MULTILINE)
_H3 = re.compile(r"^### .+$", re.MULTILINE)
_TRAILING_PAREN = re.compile(r"\s*\([^)]*\)\s*$")


def _normalise(title: str) -> str:
    return _TRAILING_PAREN.sub("", title).strip().lower()


def _parse_structure(content: str) -> list[tuple[str, int]]:
    """Return [(h2_title, h3_count_beneath)] for each H2 in content."""
    h2_matches = list(_H2.finditer(content))
    h3_matches = list(_H3.finditer(content))

    result: list[tuple[str, int]] = []
    for i, h2m in enumerate(h2_matches):
        section_start = h2m.end()
        section_end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(content)
        h3_count = sum(
            1 for h3m in h3_matches if section_start <= h3m.start() < section_end
        )
        result.append((h2m.group(1).strip(), h3_count))
    return result


def detect(content: str, source_path: Path) -> tuple[str, str, dict] | None:
    """Return (confidence, rationale, render_html_options) or None."""
    structure = _parse_structure(content)

    if len(structure) < 3:
        return None

    h2_titles = [t for t, _ in structure]
    keyword_cols = [t for t in h2_titles if _normalise(t) in COLUMN_KEYWORDS]

    if not keyword_cols:
        return None

    keyword_count = len(keyword_cols)
    h2s_with_cards = sum(1 for _, count in structure if count > 0)
    total = len(structure)

    options = {"title": source_path.stem, "columns": h2_titles}

    if keyword_count >= 3 and h2s_with_cards == total:
        kw_str = ", ".join(keyword_cols[:4])
        return (
            "high",
            f"{total} H2 columns matching status keywords ({kw_str}), each with H3 cards",
            options,
        )

    if keyword_count >= 2:
        non_kw = [t for t in h2_titles if _normalise(t) not in COLUMN_KEYWORDS]
        non_kw_str = ", ".join(non_kw) or "none"
        return (
            "medium",
            f"{keyword_count} of {total} H2s match status keywords; non-keyword: {non_kw_str}",
            options,
        )

    return (
        "low",
        f"only {keyword_count} H2 matches a status keyword (out of {total})",
        options,
    )
