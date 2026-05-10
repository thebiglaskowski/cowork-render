"""Shared markdown rendering helpers consumed by every renderer module."""

from __future__ import annotations

import html as _html
import re

from markdown_it import MarkdownIt

from cowork_render.diagrams import render_diagram

# Inline-only renderer — bold, italic, code, links, bare-URL auto-linkify.
# No block elements (no <p>, no lists, no code blocks, no blockquotes).
_INLINE = MarkdownIt("zero", {"linkify": True}).enable(
    ["emphasis", "backticks", "link", "linkify"]
)

# Block-level renderer — full CommonMark minus raw-HTML pass-through.
# Renders paragraphs, lists, code blocks, blockquotes, headings, and bare URLs.
_BLOCK = MarkdownIt("commonmark", {"html": False, "breaks": False, "linkify": True}).enable("linkify")

# Captures lang attribute (group 1) and content (group 2) for diagram detection.
_DIAGRAM_CODE_BLOCK_RE = re.compile(
    r'<pre><code(?:\s+class="language-([^"]*)")?>(.*?)</code></pre>',
    re.DOTALL,
)

# Wraps every <pre><code> block output by render_block with a copy-button container.
_CODE_BLOCK_RE = re.compile(
    r'(<pre><code(?:\s+class="[^"]*")?>.*?</code></pre>)',
    re.DOTALL,
)


def _render_diagrams_in_html(html_str: str) -> str:
    """Walk rendered HTML, replace <pre><code> blocks with diagram HTML where detectable."""
    def replace(match: re.Match) -> str:
        lang = match.group(1) or ''
        code = _html.unescape(match.group(2))
        rendered = render_diagram(code, lang)
        return rendered if rendered else match.group(0)
    return _DIAGRAM_CODE_BLOCK_RE.sub(replace, html_str)


def _wrap_code_blocks_with_copy(html: str) -> str:
    def wrap(match: re.Match) -> str:
        return (
            '<div class="code-block-wrapper">'
            '<button class="code-copy-btn" type="button" '
            'aria-label="Copy code to clipboard">Copy</button>'
            f"{match.group(1)}"
            "</div>"
        )
    return _CODE_BLOCK_RE.sub(wrap, html)


def render_inline(text: str) -> str:
    """Render inline markdown as HTML (bold, italic, code, links, bare URLs).

    No paragraph wrapping, no block elements. Use for short body content that
    lives inside a single container element (a card body, a table cell).
    """
    if not text:
        return ""
    return _INLINE.renderInline(text)


def render_block(text: str) -> str:
    """Render full block-level markdown as HTML with code-copy buttons.

    Use for long-form body content that needs paragraphs, lists, code blocks,
    blockquotes, headings, and bare-URL auto-linkification. Raw HTML in the
    source is escaped, not passed through. Each <pre><code> block is wrapped
    in a .code-block-wrapper div with a .code-copy-btn button.
    """
    if not text:
        return ""
    html_str = _BLOCK.render(text)
    html_str = _render_diagrams_in_html(html_str)
    html_str = _wrap_code_blocks_with_copy(html_str)
    return html_str


def get_copy_button_js() -> str:
    """Return the JS handler for code-block copy buttons.

    Renderers prepend this to their <script> block. Works with the
    .code-block-wrapper / .code-copy-btn markup produced by render_block.
    """
    return """\
document.querySelectorAll('.code-copy-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const wrapper = btn.closest('.code-block-wrapper');
    const code = wrapper?.querySelector('code');
    if (!code) return;
    const text = code.textContent;
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        const orig = btn.textContent;
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = orig;
          btn.classList.remove('copied');
        }, 1500);
      });
    }
  });
});"""
