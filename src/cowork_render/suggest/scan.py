"""Walk a markdown corpus and detect render-html shape candidates."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from cowork_render.suggest.detectors import dashboard, kanban
from cowork_render.suggest.detectors import timeline as timeline_det

_CONFIDENCE_RANK: dict[str, int] = {"high": 2, "medium": 1, "low": 0}
_SHAPE_PRIORITY: dict[str, int] = {"kanban": 2, "dashboard": 1, "timeline": 0}

_DETECTORS = [
    ("kanban", kanban.detect),
    ("dashboard", dashboard.detect),
    ("timeline", timeline_det.detect),
]

SKIP_DIRS = {".git", ".obsidian", "_archive", "node_modules", ".venv", "__pycache__"}


@dataclass
class Match:
    source_path: Path
    shape: str
    confidence: str
    rationale: str
    suggested_frontmatter: dict


def detect_shape(content: str, source_path: Path) -> Match | None:
    """Run all detectors against content; return the highest-confidence match or None."""
    results: list[tuple[str, str, str, dict]] = []
    for shape, detect_fn in _DETECTORS:
        result = detect_fn(content, source_path)
        if result is not None:
            confidence, rationale, options = result
            results.append((shape, confidence, rationale, options))

    if not results:
        return None

    def _sort_key(r: tuple) -> tuple[int, int]:
        shape, confidence, *_ = r
        return (_CONFIDENCE_RANK[confidence], _SHAPE_PRIORITY[shape])

    shape, confidence, rationale, options = max(results, key=_sort_key)
    suggested_fm: dict = {"render-html": shape}
    if options:
        suggested_fm["render-html-options"] = options

    return Match(
        source_path=source_path,
        shape=shape,
        confidence=confidence,
        rationale=rationale,
        suggested_frontmatter=suggested_fm,
    )


def scan(
    root: Path,
    min_confidence: str = "medium",
    shape_filter: str | None = None,
) -> tuple[int, list[Match]]:
    """Scan root for untagged markdown files that look like a known shape.

    Returns (total_scanned, matches).
    """
    matches: list[Match] = []
    scanned = 0

    for md_path in _walk_markdown(root):
        scanned += 1
        try:
            text = md_path.read_text(encoding="utf-8")
            post = frontmatter.loads(text)
            if post.metadata.get("render-html"):
                continue
            match = detect_shape(post.content, md_path)
            if match is None:
                continue
            if _CONFIDENCE_RANK[match.confidence] < _CONFIDENCE_RANK[min_confidence]:
                continue
            if shape_filter and match.shape != shape_filter:
                continue
            matches.append(match)
        except Exception:
            continue

    return scanned, matches


def _walk_markdown(root: Path):
    try:
        items = list(root.iterdir())
    except PermissionError as exc:
        print(f"warning: skipping unreadable dir {root} — {exc}", file=sys.stderr)
        return
    for item in items:
        if item.is_symlink():
            continue
        if item.is_dir():
            if item.name in SKIP_DIRS:
                continue
            yield from _walk_markdown(item)
        elif item.suffix == ".md":
            yield item
