"""Shared inline-markdown renderer used by kanban, timeline, and dashboard renderers."""

from __future__ import annotations

import html
import re

_FENCE_RE = re.compile(r'(?ms)^[ \t]*```(\w*)\n(.*?)^[ \t]*```[ \t]*$')


def _apply_inline(text: str) -> str:
    """Apply inline markdown transforms to already-HTML-escaped text."""
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(\S[^*]*?\S|\S)\*', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def _extract_ol_items(lines: list[str]) -> list[str] | None:
    """Extract numbered-list items, folding indented continuation lines into each item.

    Returns None if the lines don't start with a numbered list item.
    """
    num_re = re.compile(r'^\d+[.)]\s+')
    items: list[list[str]] = []
    current: list[str] | None = None
    for ln in lines:
        if num_re.match(ln):
            if current is not None:
                items.append(current)
            current = [num_re.sub('', ln)]
        elif current is not None:
            stripped = ln.strip()
            if stripped:
                current.append(stripped)
        else:
            return None
    if current is not None:
        items.append(current)
    return [' '.join(parts) for parts in items] if items else None


def render_inline_markdown(body: str) -> str:
    """Render markdown as HTML: bold, italic, code, links, paragraphs, and lists.

    Blank-line-separated blocks become <p> tags, bullet blocks become <ul>,
    and numbered blocks become <ol>. HTML-escaping happens first so inline
    transforms operate on safe text throughout.

    Fenced code blocks are pre-extracted to prevent triple-backtick fences
    from corrupting inline code-span regex matching.
    """
    fences: list[str] = []

    def _fence(m: re.Match) -> str:
        lang = m.group(1).strip()
        code = html.escape(m.group(2))
        idx = len(fences)
        cls = f' class="language-{html.escape(lang)}"' if lang else ''
        fences.append(f'<pre><code{cls}>{code}</code></pre>')
        return f'\x00FENCE{idx}\x00'

    body = _FENCE_RE.sub(_fence, body)

    parts = []
    for block in re.split(r"\n\n+", html.escape(body)):
        text = block.strip()
        if not text:
            continue
        lines = text.splitlines()
        non_empty = [ln for ln in lines if ln.strip()]
        if non_empty and all(re.match(r'^[-*] ', ln) for ln in non_empty):
            bullet_re = re.compile(r'^[-*] ')
            lis = ''.join(f'<li>{_apply_inline(bullet_re.sub("", ln))}</li>' for ln in non_empty)
            parts.append(f'<ul>{lis}</ul>')
        elif non_empty and all(re.match(r'^\d+[.)]\s+', ln) for ln in non_empty):
            num_re = re.compile(r'^\d+[.)]\s+')
            lis = ''.join(f'<li>{_apply_inline(num_re.sub("", ln))}</li>' for ln in non_empty)
            parts.append(f'<ol>{lis}</ol>')
        else:
            ol_items = _extract_ol_items(non_empty)
            if ol_items is not None:
                lis = ''.join(f'<li>{_apply_inline(item)}</li>' for item in ol_items)
                parts.append(f'<ol>{lis}</ol>')
            else:
                parts.append(f'<p>{_apply_inline(text)}</p>')

    result = ''.join(parts)
    for idx, fence_html in enumerate(fences):
        result = result.replace(f'\x00FENCE{idx}\x00', fence_html)
    return result
