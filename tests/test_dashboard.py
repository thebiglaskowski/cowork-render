import re
from pathlib import Path

import pytest

from cowork_render.renderers import dashboard
from cowork_render.renderers.dashboard import ProseBlock, SubsectionBlock, TableBlock

FIXTURE_MD = """\
---
render-html: dashboard
render-html-options:
  title: Test Dashboard
---

| Name | Active | Updated | Status |
|------|--------|---------|--------|
| Alpha | ✓ | 2026-01-01 | active |
| Beta | ✗ | 2025-06-01 | done |
| Gamma | ✓ | 2024-12-01 | blocked |

"""

MIXED_BLOCKS_MD = """\
---
render-html: dashboard
---

## Section A

| Name | Count |
|------|-------|
| Foo | 1 |

## Prose Only

This section has no table.

- **item-one** — description
- **item-two** — description

## Section B

| Item | Status |
|------|--------|
| X | active |

"""

MULTI_TABLE_MD = """\
---
render-html: dashboard
render-html-options:
  title: Multi Table
---

## Section A

Intro for A.

| Name | Count |
|------|-------|
| Foo | 1 |
| Bar | 2 |

## Section B

Intro for B.

| Item | Status |
|------|--------|
| X | active |
| Y | done |

"""


def _write(tmp_path: Path, content: str, name: str = "test.md") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_parse_fixture_four_columns_three_rows(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    db = dashboard.parse(path)
    assert len(db.tables) == 1
    assert len(db.tables[0].columns) == 4
    assert len(db.tables[0].rows) == 3
    assert db.tables[0].columns[0].name == "Name"
    assert db.tables[0].rows[0][0] == "Alpha"
    assert db.tables[0].rows[1][0] == "Beta"
    assert db.tables[0].rows[2][0] == "Gamma"


def test_parse_missing_signal(tmp_path):
    path = _write(tmp_path, "---\ntitle: no signal\n---\n\n# Hello\n")
    with pytest.raises(ValueError, match=str(path)):
        dashboard.parse(path)


def test_parse_missing_table(tmp_path):
    content = "---\nrender-html: dashboard\n---\n\n# No table here\n\nJust prose.\n"
    path = _write(tmp_path, content)
    with pytest.raises(ValueError, match=str(path)):
        dashboard.parse(path)


def test_type_detection_boolean(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    db = dashboard.parse(path)
    assert db.tables[0].columns[1].name == "Active"
    assert db.tables[0].columns[1].detected_type == "boolean"


def test_type_detection_date(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    db = dashboard.parse(path)
    assert db.tables[0].columns[2].name == "Updated"
    assert db.tables[0].columns[2].detected_type == "date"


def test_type_detection_status(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    db = dashboard.parse(path)
    assert db.tables[0].columns[3].name == "Status"
    assert db.tables[0].columns[3].detected_type == "status"


def test_column_types_override(tmp_path):
    content = """\
---
render-html: dashboard
render-html-options:
  column_types:
    Active: text
---

| Name | Active |
|------|--------|
| Alpha | ✓ |
| Beta | ✗ |
| Gamma | ✓ |

"""
    path = _write(tmp_path, content)
    db = dashboard.parse(path)
    assert db.tables[0].columns[1].detected_type == "text"


def test_parse_multi_table(tmp_path):
    path = _write(tmp_path, MULTI_TABLE_MD)
    db = dashboard.parse(path)
    assert len(db.tables) == 2
    assert db.tables[0].heading == "Section A"
    assert db.tables[0].notes_md == "Intro for A."
    assert db.tables[0].columns[0].name == "Name"
    assert db.tables[0].rows[0][0] == "Foo"
    assert db.tables[1].heading == "Section B"
    assert db.tables[1].columns[1].detected_type == "status"


def test_render_produces_valid_html(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = dashboard.render(path)
    assert result.startswith("<!DOCTYPE html>")
    assert 'class="dashboard"' in result
    assert "Alpha" in result
    assert '<input type="search"' in result
    assert "Test Dashboard" in result


def test_render_escapes_hostile_content(tmp_path):
    content = """\
---
render-html: dashboard
---

| Name |
|------|
| <script>alert(1)</script> |

"""
    path = _write(tmp_path, content)
    result = dashboard.render(path)
    body_section = result.split("<script>")[0]
    assert "&lt;script&gt;" in body_section
    assert "<script>alert(1)</script>" not in body_section


def test_cell_class_bool_yes(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = dashboard.render(path)
    assert 'class="cell-bool-yes"' in result


def test_sortable_header_markup(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = dashboard.render(path)
    assert 'class="sortable"' in result
    assert 'data-col="0"' in result
    assert 'data-type="text"' in result


def test_render_multi_table(tmp_path):
    path = _write(tmp_path, MULTI_TABLE_MD)
    result = dashboard.render(path)
    assert result.count('class="dashboard"') == 2
    assert 'data-table-index="0"' in result
    assert 'data-table-index="1"' in result
    assert 'class="section-heading"' in result
    assert "Section A" in result
    assert "Section B" in result
    assert "Foo" in result
    assert "active" in result


def test_parse_prose_section(tmp_path):
    path = _write(tmp_path, MIXED_BLOCKS_MD)
    db = dashboard.parse(path)
    assert len(db.tables) == 2
    assert len(db.blocks) == 3
    assert isinstance(db.blocks[0], TableBlock)
    assert isinstance(db.blocks[1], ProseBlock)
    assert isinstance(db.blocks[2], TableBlock)
    assert db.blocks[1].heading == "Prose Only"
    assert "item-one" in db.blocks[1].body_md


def test_render_prose_section(tmp_path):
    path = _write(tmp_path, MIXED_BLOCKS_MD)
    result = dashboard.render(path)
    assert result.count('class="dashboard"') == 2
    assert "Prose Only" in result
    assert '<ul>' in result
    assert '<li>' in result
    assert "item-one" in result


def test_render_inline_markdown_in_cells(tmp_path):
    content = """\
---
render-html: dashboard
---

| Name | Endpoint |
|------|----------|
| Spotify | `https://example.com/mcp` |

"""
    path = _write(tmp_path, content)
    result = dashboard.render(path)
    assert "<code>https://example.com/mcp</code>" in result
    assert "`https://example.com/mcp`" not in result


def test_render_idempotent(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    r1 = dashboard.render(path)
    r2 = dashboard.render(path)
    r1 = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC', 'DATE', r1)
    r2 = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC', 'DATE', r2)
    assert r1 == r2


PREAMBLE_BLOCKS_MD = """\
---
render-html: dashboard
---

Intro paragraph.

- **bold-item** description one
- **bold-item** description two

```bash
echo hello
```

## Section A

| Name | Count |
|------|-------|
| Foo | 1 |

"""

H3_WITH_H4_SUBS_MD = """\
---
render-html: dashboard
---

### Section 3

Intro for section 3.

#### 3a: First subsection

Notes for 3a.

| Name | Value |
|------|-------|
| Alpha | 1 |

#### 3b: Second subsection

| Name | Value |
|------|-------|
| Beta | 2 |

"""

H3_WITHOUT_SUBS_MD = """\
---
render-html: dashboard
---

### Plain Section

Notes here.

| Name | Value |
|------|-------|
| Gamma | 3 |

"""


def test_dashboard_commentary_uses_render_block(tmp_path):
    path = _write(tmp_path, PREAMBLE_BLOCKS_MD)
    result = dashboard.render(path)
    assert "<ul>" in result
    assert "<li>" in result
    assert "<pre>" in result
    assert "<strong>bold-item</strong>" in result


def test_parse_h3_with_h4_subsections(tmp_path):
    path = _write(tmp_path, H3_WITH_H4_SUBS_MD)
    db = dashboard.parse(path)
    assert len(db.tables) == 1
    tb = db.tables[0]
    assert tb.heading == "Section 3"
    assert len(tb.subsections) == 2
    assert isinstance(tb.subsections[0], SubsectionBlock)
    assert tb.subsections[0].heading == "3a: First subsection"
    assert tb.subsections[1].heading == "3b: Second subsection"
    assert len(tb.subsections[0].rows) == 1
    assert len(tb.subsections[1].rows) == 1


def test_parse_h3_without_subsections(tmp_path):
    path = _write(tmp_path, H3_WITHOUT_SUBS_MD)
    db = dashboard.parse(path)
    assert len(db.tables) == 1
    tb = db.tables[0]
    assert tb.heading == "Plain Section"
    assert len(tb.subsections) == 0
    assert len(tb.rows) == 1


def test_preamble_pre_has_white_space_pre_wrap(tmp_path):
    from cowork_render.renderers.dashboard import _CSS
    assert "white-space: pre-wrap" in _CSS


def test_code_block_wrapper_pre_overrides_to_white_space_pre(tmp_path):
    from cowork_render.renderers.dashboard import _CSS
    wrap_pos = _CSS.index(".code-block-wrapper pre")
    preamble_pos = _CSS.index(".preamble pre")
    assert wrap_pos > preamble_pos, ".code-block-wrapper pre must come after .preamble pre to override it"
    wrapper_snippet = _CSS[wrap_pos:wrap_pos + 200]
    assert "white-space: pre;" in wrapper_snippet
