import re
from pathlib import Path

import pytest

from cowork_render.renderers import dashboard

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


def _write(tmp_path: Path, content: str, name: str = "test.md") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_parse_fixture_four_columns_three_rows(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    db = dashboard.parse(path)
    assert len(db.columns) == 4
    assert len(db.rows) == 3
    assert db.columns[0].name == "Name"
    assert db.rows[0][0] == "Alpha"
    assert db.rows[1][0] == "Beta"
    assert db.rows[2][0] == "Gamma"


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
    assert db.columns[1].name == "Active"
    assert db.columns[1].detected_type == "boolean"


def test_type_detection_date(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    db = dashboard.parse(path)
    assert db.columns[2].name == "Updated"
    assert db.columns[2].detected_type == "date"


def test_type_detection_status(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    db = dashboard.parse(path)
    assert db.columns[3].name == "Status"
    assert db.columns[3].detected_type == "status"


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
    assert db.columns[1].detected_type == "text"


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


def test_render_idempotent(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    r1 = dashboard.render(path)
    r2 = dashboard.render(path)
    r1 = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC', 'DATE', r1)
    r2 = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC', 'DATE', r2)
    assert r1 == r2
