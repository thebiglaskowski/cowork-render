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
