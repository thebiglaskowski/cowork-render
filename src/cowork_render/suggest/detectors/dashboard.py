"""Dashboard shape detector — pipe tables with typed header columns."""

from __future__ import annotations

import re
from pathlib import Path

TYPED_HEADERS = {
    "status", "priority", "owner", "assignee", "due", "due date",
    "date", "type", "category", "label", "tag", "tags", "score",
    "count", "risk", "severity", "progress", "effort", "impact",
}

_SEP_ROW = re.compile(r"^\|[\s\-:|]+\|$")


def detect(content: str, source_path: Path) -> tuple[str, str, dict] | None:
    """Return (confidence, rationale, render_html_options) or None."""
    lines = content.splitlines()
    best_typed = 0
    best_data_rows = 0

    i = 0
    while i < len(lines):
        if not lines[i].strip().startswith("|"):
            i += 1
            continue

        table_lines: list[str] = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            table_lines.append(lines[i].strip())
            i += 1

        if len(table_lines) < 3:
            continue
        if not _SEP_ROW.match(table_lines[1]):
            continue

        headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
        data_rows = len(table_lines) - 2
        typed_count = sum(1 for h in headers if h.lower() in TYPED_HEADERS)

        if typed_count > best_typed or (typed_count == best_typed and data_rows > best_data_rows):
            best_typed = typed_count
            best_data_rows = data_rows

    if best_typed == 0:
        return None

    if best_typed >= 2 and best_data_rows >= 3:
        return (
            "high",
            f"pipe table with {best_typed} typed columns and {best_data_rows} data rows",
            {"title": source_path.stem},
        )

    if best_typed >= 1 and best_data_rows >= 2:
        return (
            "medium",
            f"pipe table with {best_typed} typed column(s) and {best_data_rows} data rows",
            {"title": source_path.stem},
        )

    return None
