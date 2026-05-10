import re
from pathlib import Path

import pytest

from cowork_render.renderers import timeline

FIXTURE_MD = """\
---
render-html: timeline
render-html-options:
  title: Test Timeline
---

# Test Timeline

## Format

Entries use the H3 date-prefix convention.

### 2026-05-09 — Decision Alpha

**Decision:** Use regex-based parsing.

**Why:** Keeps dependencies minimal.

**Principle in play:** YAGNI

### 2026-05-08 — Decision Beta

**Decision:** Store raw markdown in data attributes.

**Why:** Enables lossless round-trip export.

### 2026-05-07 — Decision Gamma

**Decision:** Dark theme only.

**Why:** Matches existing audit family palette.

"""


def _write(tmp_path: Path, content: str, name: str = "test.md") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_parse_fixture_three_entries(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    tl = timeline.parse(path)
    assert len(tl.entries) == 3
    assert tl.entries[0].date == "2026-05-09"
    assert tl.entries[0].title == "Decision Alpha"
    assert tl.entries[1].date == "2026-05-08"
    assert tl.entries[1].title == "Decision Beta"
    assert tl.entries[2].date == "2026-05-07"
    assert tl.entries[2].title == "Decision Gamma"


def test_parse_missing_signal(tmp_path):
    path = _write(tmp_path, "---\ntitle: no signal\n---\n\n# Hello\n")
    with pytest.raises(ValueError, match=str(path)):
        timeline.parse(path)


def test_parse_no_entries(tmp_path):
    content = "---\nrender-html: timeline\n---\n\n# Empty\n\nNo dated entries here.\n"
    path = _write(tmp_path, content)
    tl = timeline.parse(path)
    assert tl.entries == []


def test_parse_field_extraction(tmp_path):
    content = """\
---
render-html: timeline
---

### 2026-05-09 — Alpha

**Decision:** Use regex parsing.

**Why:** Simple approach.

**Principle in play:** YAGNI

"""
    path = _write(tmp_path, content)
    tl = timeline.parse(path)
    assert len(tl.entries) == 1
    fields = {f.name: f.value_md for f in tl.entries[0].fields}
    assert set(fields.keys()) == {"Decision", "Why", "Principle in play"}
    assert fields["Decision"] == "Use regex parsing."
    assert fields["Why"] == "Simple approach."


def test_parse_multiline_field_value(tmp_path):
    content = """\
---
render-html: timeline
---

### 2026-05-09 — Alpha

**Decision:** This is a long decision
that continues on the next line.

It has a second paragraph.

**Why:** Short reason.

"""
    path = _write(tmp_path, content)
    tl = timeline.parse(path)
    assert len(tl.entries[0].fields) == 2
    decision_value = tl.entries[0].fields[0].value_md
    assert "long decision" in decision_value
    assert "second paragraph" in decision_value


def test_parse_tag_extraction(tmp_path):
    content = """\
---
render-html: timeline
render-html-options:
  tag_field: "Principle in play"
---

### 2026-05-09 — Alpha

**Decision:** Something.

**Principle in play:** Greene Law 47, Cialdini reciprocity

"""
    path = _write(tmp_path, content)
    tl = timeline.parse(path)
    assert tl.entries[0].tags == ["Greene Law 47", "Cialdini reciprocity"]


def test_parse_preamble(tmp_path):
    content = """\
---
render-html: timeline
---

# My Timeline

## Format

Log format description here.

### 2026-05-09 — First entry

**Decision:** Something.

"""
    path = _write(tmp_path, content)
    tl = timeline.parse(path)
    assert "My Timeline" in tl.preamble_md
    assert "Log format description" in tl.preamble_md
    assert "First entry" not in tl.preamble_md


def test_render_produces_valid_html(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = timeline.render(path)
    assert result.startswith("<!DOCTYPE html>")
    assert 'class="spine"' in result
    assert 'class="entry"' in result
    assert 'data-date="2026-05-09"' in result
    assert "Decision Alpha" in result
    assert '<input type="date"' in result


def test_render_escapes_hostile_content(tmp_path):
    content = """\
---
render-html: timeline
---

### 2026-05-09 — Hostile

**Decision:** <script>alert(1)</script>

"""
    path = _write(tmp_path, content)
    result = timeline.render(path)
    body_section = result.split("<script>")[0]
    assert "&lt;script&gt;" in body_section
    assert "<script>alert(1)</script>" not in body_section


def test_render_filter_inputs_present(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = timeline.render(path)
    assert result.count('<input type="date"') == 2
    assert '<input type="search"' in result


def test_render_sort_order_newest_first(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = timeline.render(path)
    idx_newest = result.index('data-date="2026-05-09"')
    idx_oldest = result.index('data-date="2026-05-07"')
    assert idx_newest < idx_oldest


def test_render_idempotent(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    r1 = timeline.render(path)
    r2 = timeline.render(path)
    r1 = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC', 'DATE', r1)
    r2 = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC', 'DATE', r2)
    assert r1 == r2
