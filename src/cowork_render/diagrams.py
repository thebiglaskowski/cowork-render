"""ASCII diagram detection and rendering — tree, vertical-flow, horizontal-flow."""

from __future__ import annotations

import html
import re


# Opt-out fence info strings — these code blocks are skipped by diagram detection
_OPT_OUT_LANGS = {"noformat", "text-only", "plain", "raw"}


def render_diagram(content: str, fence_lang: str | None = None) -> str | None:
    """Try each diagram parser in order. Return rendered HTML if any matches, else None.

    Order matters: tree is checked first (most specific pattern), then vertical flow,
    then horizontal flow. Each parser returns None if its pattern doesn't match.

    A fence_lang in _OPT_OUT_LANGS skips detection entirely — the code block renders
    as standard <pre><code>.
    """
    if fence_lang and fence_lang.lower() in _OPT_OUT_LANGS:
        return None

    if (rendered := _render_tree(content)) is not None:
        return rendered
    if (rendered := _render_flow_vertical(content)) is not None:
        return rendered
    if (rendered := _render_flow_horizontal(content)) is not None:
        return rendered
    return None


def _render_tree(content: str) -> str | None:
    """Detect and render an ASCII tree as a nested <ul>.

    Heuristic: at least 2 lines contain ├, └, or │ tree markers.
    """
    tree_markers = ('├', '└', '│', '┬', '┼', '┤', '┴')
    lines = [line.rstrip() for line in content.split('\n') if line.rstrip()]
    if sum(1 for line in lines if any(m in line for m in tree_markers)) < 2:
        return None

    # Parse each line into (depth, label)
    # Depth = column position of the first tree marker or label character
    # Label = text after stripping tree markers and leading whitespace
    parsed = []
    for line in lines:
        # Find the leftmost non-whitespace, non-tree-marker character
        depth = 0
        for i, ch in enumerate(line):
            if ch.isspace() or ch in tree_markers or ch == '|':
                continue
            depth = i
            break
        # Strip leading whitespace + tree markers to extract label
        label = re.sub(r'^[\s│|├└┬┼┤┴─]+', '', line).strip()
        # Skip lines that have only tree markers (visual connectors with no label)
        if not label:
            continue
        parsed.append((depth, label))

    if len(parsed) < 2:
        return None

    return _build_tree_html(parsed)


def _build_tree_html(parsed: list[tuple[int, str]]) -> str:
    """Build nested <ul> HTML from a list of (depth, label) tuples."""
    unique_depths = sorted(set(d for d, _ in parsed))
    depth_to_level = {d: i for i, d in enumerate(unique_depths)}

    parts = ['<div class="diagram-tree-wrap"><ul class="diagram-tree">']
    current_level = 0
    for depth, label in parsed:
        target_level = depth_to_level[depth]
        # Close levels until we're at the target's parent
        while current_level > target_level:
            parts.append('</li></ul>')
            current_level -= 1
        # Open new levels if we're going deeper
        if target_level > current_level:
            parts.append('<ul>')
            current_level = target_level
        else:
            # Same level — close previous <li>
            if parts[-1] != '<ul>' and not parts[-1].endswith('">'):
                parts.append('</li>')
        parts.append(f'<li>{html.escape(label)}')
    # Close remaining open <li> and <ul> tags
    while current_level >= 0:
        parts.append('</li></ul>')
        current_level -= 1
    parts.append('</div>')
    return ''.join(parts)


def _render_flow_vertical(content: str) -> str | None:
    """Detect and render a vertical-flow diagram as a stack of cards with arrow connectors.

    Heuristic: content contains 2+ ↓ characters on lines by themselves (whitespace allowed).
    """
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    arrow_lines = sum(1 for line in lines if re.fullmatch(r'[↓⬇]+', line))
    if arrow_lines < 2:
        return None

    # Filter out arrow-only lines, keep label lines
    labels = [line for line in lines if not re.fullmatch(r'[↓⬇]+', line)]
    if len(labels) < 3:
        return None

    parts = ['<div class="diagram-flow-v">']
    for label in labels:
        parts.append(f'<div class="flow-step">{html.escape(label)}</div>')
    parts.append('</div>')
    return ''.join(parts)


def _render_flow_horizontal(content: str) -> str | None:
    """Detect and render a horizontal-flow diagram as a flex row of cards with arrow connectors.

    Heuristic: content contains 2+ → characters as separators between text segments.
    """
    # Normalize: join all lines into one stream, then split on →
    flat = re.sub(r'\s*\n\s*', ' ', content.strip())
    if flat.count('→') < 2 and flat.count('⟶') < 2:
        return None
    # Split on → or ⟶ (with optional surrounding spaces)
    segments = [s.strip() for s in re.split(r'\s*[→⟶]\s*', flat) if s.strip()]
    if len(segments) < 3:
        return None

    parts = ['<div class="diagram-flow-h">']
    for i, segment in enumerate(segments):
        if i > 0:
            parts.append('<div class="flow-arrow" aria-hidden="true">→</div>')
        parts.append(f'<div class="flow-step">{html.escape(segment)}</div>')
    parts.append('</div>')
    return ''.join(parts)
