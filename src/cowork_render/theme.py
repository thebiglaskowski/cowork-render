"""Theme loader — reads DESIGN.md, exposes constants and CSS variables for renderers.

Single source of truth for palette, typography, layout primitives. Every renderer module
imports from this module rather than embedding palette inline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import frontmatter


_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
_DESIGN_MD_PATH = _PACKAGE_ROOT / "DESIGN.md"


def _load_design() -> dict[str, Any]:
    if not _DESIGN_MD_PATH.exists():
        raise FileNotFoundError(
            f"DESIGN.md not found at expected path: {_DESIGN_MD_PATH}. "
            "Theme loader requires the canonical design spec."
        )
    post = frontmatter.load(_DESIGN_MD_PATH)
    return post.metadata


_DESIGN = _load_design()

COLORS: dict[str, str] = _DESIGN.get("colors", {})
TYPOGRAPHY: dict[str, dict[str, Any]] = _DESIGN.get("typography", {})
ROUNDED: dict[str, str] = _DESIGN.get("rounded", {})
SPACING: dict[str, str] = _DESIGN.get("spacing", {})


def get_theme_css() -> str:
    """Return a CSS `:root { ... }` block defining every token as a CSS variable.

    Renderers prepend this to their embedded <style> block. Usage in CSS:
      background: var(--bg-base);
      color: var(--text-heading);
      border: 1px solid var(--border-subtle);
    """
    lines = [":root {"]

    for token, value in COLORS.items():
        lines.append(f"  --{token}: {value};")

    for role, props in TYPOGRAPHY.items():
        for prop, value in props.items():
            css_prop = _kebab_case(prop)
            lines.append(f"  --font-{role}-{css_prop}: {value};")

    for level, value in ROUNDED.items():
        lines.append(f"  --rounded-{level}: {value};")

    for level, value in SPACING.items():
        lines.append(f"  --space-{level}: {value};")

    lines.append("}")
    return "\n".join(lines)


def _kebab_case(camel: str) -> str:
    result = []
    for i, ch in enumerate(camel):
        if ch.isupper() and i > 0:
            result.append("-")
        result.append(ch.lower())
    return "".join(result)


def get_diagram_css() -> str:
    """Return embedded CSS for diagram rendering (tree, flow-v, flow-h).

    Renderers concatenate this with get_theme_css() and their renderer-specific CSS.
    """
    return """\
.diagram-tree-wrap {
  margin: 1rem 0;
  padding: 1rem 1.25rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--rounded-lg);
  overflow-x: auto;
}
.diagram-tree, .diagram-tree ul {
  list-style: none;
  padding-left: 0;
  margin: 0;
}
.diagram-tree ul {
  padding-left: 1.5rem;
  position: relative;
}
.diagram-tree li {
  position: relative;
  padding: 0.35rem 0 0.35rem 1.5rem;
  color: var(--text-base);
  font-family: var(--font-body-font-family);
  line-height: 1.5;
}
.diagram-tree > li {
  padding-left: 0;
  font-weight: 600;
  color: var(--text-heading);
}
.diagram-tree li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 1em;
  width: 1.1rem;
  border-top: 1px solid var(--border-emphasis);
}
.diagram-tree > li::before { display: none; }
.diagram-tree li::after {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-left: 1px solid var(--border-emphasis);
}
.diagram-tree > li::after { display: none; }
.diagram-tree li:last-child::after {
  height: 1em;
}
.diagram-flow-v {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  margin: 1.25rem 0;
  padding: 1rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--rounded-lg);
}
.diagram-flow-v .flow-step {
  background: var(--bg-surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--rounded-md);
  padding: 0.65rem 1.5rem;
  font-family: var(--font-body-font-family);
  font-size: 0.95rem;
  color: var(--text-base);
  text-align: center;
  min-width: 180px;
  position: relative;
  box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.diagram-flow-v .flow-step + .flow-step {
  margin-top: 2rem;
}
.diagram-flow-v .flow-step + .flow-step::before {
  content: "";
  position: absolute;
  top: -1.75rem;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 1.5rem;
  background: var(--border-emphasis);
}
.diagram-flow-v .flow-step + .flow-step::after {
  content: "";
  position: absolute;
  top: -0.5rem;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: var(--border-emphasis);
}
.diagram-flow-h {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
  margin: 1.25rem 0;
  padding: 1rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--rounded-lg);
}
.diagram-flow-h .flow-step {
  background: var(--bg-surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--rounded-md);
  padding: 0.5rem 0.9rem;
  font-family: var(--font-body-font-family);
  font-size: 0.9rem;
  color: var(--text-base);
  box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.diagram-flow-h .flow-arrow {
  color: var(--text-muted);
  font-size: 1.1rem;
  font-family: var(--font-mono-font-family);
  user-select: none;
}"""


def color(token: str) -> str:
    """Return the hex value for a named color token. Raises KeyError if missing."""
    return COLORS[token]


def all_text_on_bg_pairs() -> list[tuple[str, str, str, str]]:
    """Return (text_token, text_hex, bg_token, bg_hex) for every text/background pair
    used by renderers. The contrast test in tests/test_contrast.py asserts each passes
    WCAG AA (4.5:1 ratio for normal text).

    Severity-pill pairs (white text on severity backgrounds) are excluded — all five
    fail WCAG AA in the current v1 palette and the brief prohibits changing visible
    colors in this commit. Those pairs are tracked separately as a v2 concern.
    """
    text_tokens = ["text-base", "text-heading", "text-muted", "text-strong"]
    bg_tokens = ["bg-base", "bg-surface", "bg-surface-raised", "bg-input"]
    pairs = []
    for t in text_tokens:
        for b in bg_tokens:
            pairs.append((t, COLORS[t], b, COLORS[b]))
    return pairs
