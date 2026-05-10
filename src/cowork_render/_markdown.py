"""Shared markdown rendering helpers consumed by every renderer module."""

from __future__ import annotations

import re

from markdown_it import MarkdownIt

# Inline-only renderer — bold, italic, code, links, bare-URL auto-linkify.
# No block elements (no <p>, no lists, no code blocks, no blockquotes).
_INLINE = MarkdownIt("zero", {"linkify": True}).enable(
    ["emphasis", "backticks", "link", "linkify"]
)

# Block-level renderer — full CommonMark minus raw-HTML pass-through.
# Renders paragraphs, lists, code blocks, blockquotes, headings, and bare URLs.
_BLOCK = MarkdownIt("commonmark", {"html": False, "breaks": False, "linkify": True}).enable("linkify")

# Wraps every <pre><code> block output by render_block with a copy-button container.
_CODE_BLOCK_RE = re.compile(
    r'(<pre><code(?:\s+class="[^"]*")?>.*?</code></pre>)',
    re.DOTALL,
)


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
    return _wrap_code_blocks_with_copy(_BLOCK.render(text))


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
