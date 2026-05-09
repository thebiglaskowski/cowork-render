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
