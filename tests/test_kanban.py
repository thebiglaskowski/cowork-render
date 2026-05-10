import html
import re
from pathlib import Path

import pytest

from cowork_render.renderers import kanban

FIXTURE_MD = """\
---
render-html: kanban
render-html-options:
  title: Test Board
---

# Test Board Title

## Now

### Card A

Body A.

### Card B

Body B.

## Next

### Card C

Body C.

## Later

"""


def _write(tmp_path: Path, content: str, name: str = "test.md") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_parse_fixture(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    board = kanban.parse(path)
    assert len(board.columns) == 3
    assert board.columns[0].name == "Now"
    assert len(board.columns[0].cards) == 2
    assert board.columns[0].cards[0].title == "Card A"
    assert board.columns[0].cards[0].body == "Body A."
    assert board.columns[1].name == "Next"
    assert len(board.columns[1].cards) == 1
    assert board.columns[1].cards[0].title == "Card C"
    assert board.columns[2].name == "Later"
    assert len(board.columns[2].cards) == 0


def test_parse_missing_signal(tmp_path):
    path = _write(tmp_path, "---\ntitle: no signal\n---\n\n# Hello\n")
    with pytest.raises(ValueError, match=str(path)):
        kanban.parse(path)


def test_parse_wrong_signal(tmp_path):
    path = _write(tmp_path, "---\nrender-html: dashboard\n---\n\n# Hello\n")
    with pytest.raises(ValueError, match="kanban"):
        kanban.parse(path)


def test_render_produces_valid_html(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = kanban.render(path)
    assert result.startswith("<!DOCTYPE html>")
    assert "Now" in result
    assert "Next" in result
    assert "Card A" in result
    assert "Card B" in result
    assert "Card C" in result


def test_render_escapes_html(tmp_path):
    content = (
        "---\nrender-html: kanban\n---\n\n"
        "## Now\n\n### Safe card\n\n<script>alert(1)</script>\n\n"
    )
    path = _write(tmp_path, content)
    result = kanban.render(path)
    # everything before the embedded JS <script> block
    body_section = result.split("<script>")[0]
    assert "&lt;script&gt;" in body_section
    assert "<script>alert(1)</script>" not in body_section


def test_render_idempotent(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    r1 = kanban.render(path)
    r2 = kanban.render(path)

    def normalize(s: str) -> str:
        s = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "UUID", s)
        s = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", "DATE", s)
        return s

    assert normalize(r1) == normalize(r2)


def test_parse_extracts_raw_frontmatter_and_preamble(tmp_path):
    content = """\
---
render-html: kanban
render-html-options:
  title: Test Board
---

# My Preamble

Some preamble text.

## Now

### A card

Body.

"""
    path = _write(tmp_path, content)
    board = kanban.parse(path)
    assert "render-html: kanban" in board.raw_frontmatter
    assert "render-html-options" in board.raw_frontmatter
    assert "---" not in board.raw_frontmatter  # delimiters stripped
    assert "# My Preamble" in board.raw_preamble
    assert "Some preamble text." in board.raw_preamble


def test_render_script_injection_safe(tmp_path):
    content = (
        "---\n"
        'render-html: kanban\n'
        'render-html-options:\n'
        '  title: "</script><img src=x onerror=alert(1)>"\n'
        "---\n\n"
        "## Now\n\n### A card\n\nSafe body.\n\n"
    )
    path = _write(tmp_path, content)
    result = kanban.render(path)
    # </script> must never appear inside a <script> block in a way that could close it
    # The title injection attempt should be neutralized
    assert "</script><img" not in result


def test_parse_column_ordering_with_options(tmp_path):
    content = """\
---
render-html: kanban
render-html-options:
  columns: [Now, Next, Later, Cut]
---

## Cut

### Cut card

## Now

### Now card

## Later

### Later card

## Next

### Next card

"""
    path = _write(tmp_path, content)
    board = kanban.parse(path)
    assert [c.name for c in board.columns] == ["Now", "Next", "Later", "Cut"]


# --- v1.1 tests: inline markdown rendering ---


def test_markdown_render_bold():
    result = kanban._render_card_body_markdown("**Why it matters.**")
    assert "<strong>Why it matters.</strong>" in result
    assert "**" not in result


def test_markdown_render_italic():
    result = kanban._render_card_body_markdown("*emphasis*")
    assert "<em>emphasis</em>" in result


def test_markdown_render_inline_code():
    result = kanban._render_card_body_markdown("`current-session.md`")
    assert "<code>current-session.md</code>" in result


def test_markdown_render_link():
    result = kanban._render_card_body_markdown(
        "[next-actions.md](../autoscriptstudio/next-actions.md)"
    )
    assert '<a href="../autoscriptstudio/next-actions.md">next-actions.md</a>' in result


def test_markdown_render_paragraph_splitting():
    body = "Para one.\n\nPara two.\n\nPara three."
    result = kanban._render_card_body_markdown(body)
    assert result.count("<p>") == 3
    assert result.count("</p>") == 3
    assert "\n\n" not in result


def test_markdown_render_html_escape_in_bold():
    body = "**<script>alert(1)</script>**"
    result = kanban._render_card_body_markdown(body)
    assert "&lt;script&gt;" in result
    assert "<strong>" in result and "</strong>" in result
    assert "<script>" not in result


def test_markdown_render_whitespace_asterisk_no_italic():
    result = kanban._render_card_body_markdown("5 * 7 = 35")
    assert "<em>" not in result


def test_data_markdown_body_roundtrip(tmp_path):
    original_body = "**bold** and *italic* and `code`"
    content = (
        "---\nrender-html: kanban\n---\n\n"
        f"## Now\n\n### Card Title\n\n{original_body}\n\n"
    )
    path = _write(tmp_path, content)
    result = kanban.render(path)
    expected_attr = html.escape(original_body, quote=True)
    assert f'data-markdown-body="{expected_attr}"' in result


def test_articles_have_data_markdown_body(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = kanban.render(path)
    articles = re.findall(
        r'<article class="card"[^>]*data-markdown-body="([^"]*)"', result
    )
    non_empty = [a for a in articles if a]
    # FIXTURE_MD has three cards with bodies: Body A., Body B., Body C.
    assert len(non_empty) == 3


# --- v1.2 tests: render_inline protects code-spans ---

def test_markdown_render_code_span_protects_link_inside():
    result = kanban._render_card_body_markdown("`[text](path.md)`")
    assert "<code>[text](path.md)</code>" in result
    assert "<a href" not in result


def test_markdown_render_inline_markers_still_work_outside_code():
    result = kanban._render_card_body_markdown("**bold** and `code` and [link](url)")
    assert "<strong>bold</strong>" in result
    assert "<code>code</code>" in result
    assert '<a href="url">link</a>' in result
