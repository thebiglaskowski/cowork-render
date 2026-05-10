"""Shared markdown rendering helpers consumed by every renderer module."""

from __future__ import annotations

from markdown_it import MarkdownIt

# Inline-only renderer for card-sized contexts (kanban card bodies, dashboard cell content).
# Renders <strong>, <em>, <code>, <a> but does NOT promote text into <p> elements or render
# block-level structures (lists, code blocks, headings, blockquotes).
_INLINE = MarkdownIt("zero").enable(["emphasis", "backticks", "link"])

# Block-level renderer for prose-rich contexts (dashboard commentary panels).
# Renders paragraphs, lists, code blocks, blockquotes, headings — full CommonMark
# minus raw-HTML pass-through.
_BLOCK = MarkdownIt("commonmark", {"html": False, "breaks": False, "linkify": False})


def render_inline(text: str) -> str:
    """Render inline markdown markers as HTML. No paragraph wrapping, no block elements.

    Use for short body content where the rendered HTML is meant to live inside a single
    container element (a card body, a table cell). Bold/italic/code/link only.
    """
    if not text:
        return ""
    return _INLINE.renderInline(text)


def render_block(text: str) -> str:
    """Render full block-level markdown as HTML.

    Use for long-form body content that needs paragraphs, lists, code blocks, blockquotes,
    headings. Returns HTML with all block elements wrapped (e.g. <p>...</p>,
    <ul><li>...</li></ul>). Raw HTML in the source is escaped, not passed through.
    """
    if not text:
        return ""
    return _BLOCK.render(text)
