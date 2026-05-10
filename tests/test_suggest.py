"""Tests for shape detectors and detect_shape dispatch in cowork_render.suggest."""

from pathlib import Path

from cowork_render.suggest.detectors import dashboard, kanban
from cowork_render.suggest.detectors import timeline as tl
from cowork_render.suggest.scan import detect_shape

FAKE = Path("/tmp/fake.md")


# ---------------------------------------------------------------------------
# Kanban detector
# ---------------------------------------------------------------------------

def test_kanban_high_confidence_on_status_columns_with_cards():
    content = "## Backlog\n\n### Task A\n\ndesc\n\n## Done\n\n### Task B\n"
    confidence, _, _ = kanban.detect(content, FAKE)
    assert confidence == "high"


def test_kanban_medium_confidence_on_one_keyword_column():
    content = "## Backlog\n\n### Task A\n\n## Random Heading\n\n### Task B\n"
    confidence, _, _ = kanban.detect(content, FAKE)
    assert confidence == "medium"


def test_kanban_returns_none_when_no_h2():
    assert kanban.detect("# Title\n\n### Card\n", FAKE) is None


def test_kanban_returns_none_when_no_cards():
    content = "## Backlog\n\nSome prose.\n\n## Done\n\nMore prose.\n"
    assert kanban.detect(content, FAKE) is None


def test_kanban_normalises_trailing_count():
    content = "## Done (3)\n\n### Task A\n\n## Backlog (7)\n\n### Task B\n"
    confidence, _, _ = kanban.detect(content, FAKE)
    assert confidence == "high"


# ---------------------------------------------------------------------------
# Dashboard detector
# ---------------------------------------------------------------------------

def test_dashboard_high_confidence_on_typed_columns():
    content = (
        "| Task | Status | Priority | Owner |\n"
        "|------|--------|----------|-------|\n"
        "| A    | Done   | High     | Joe   |\n"
        "| B    | Open   | Low      | Jane  |\n"
        "| C    | Blocked| Med      | Bob   |\n"
    )
    confidence, _, _ = dashboard.detect(content, FAKE)
    assert confidence == "high"


def test_dashboard_medium_confidence_on_one_typed_column():
    content = (
        "| Task | Status |\n"
        "|------|--------|\n"
        "| A    | Done   |\n"
        "| B    | Open   |\n"
    )
    confidence, _, _ = dashboard.detect(content, FAKE)
    assert confidence == "medium"


def test_dashboard_returns_none_for_plain_prose():
    assert dashboard.detect("# Title\n\nJust prose.\n", FAKE) is None


def test_dashboard_returns_none_for_table_without_typed_headers():
    content = (
        "| Name | Value |\n"
        "|------|-------|\n"
        "| A    | 1     |\n"
        "| B    | 2     |\n"
        "| C    | 3     |\n"
    )
    assert dashboard.detect(content, FAKE) is None


# ---------------------------------------------------------------------------
# Timeline detector
# ---------------------------------------------------------------------------

def test_timeline_high_confidence_on_three_date_headings():
    content = (
        "### 2026-01-01 — First\n\nContent.\n"
        "### 2026-01-02 — Second\n\nContent.\n"
        "### 2026-01-03 — Third\n\nContent.\n"
    )
    confidence, _, options = tl.detect(content, FAKE)
    assert confidence == "high"
    assert options["entry_heading_level"] == 3


def test_timeline_medium_confidence_on_two_date_headings():
    content = (
        "### 2026-01-01 — First\n\nContent.\n"
        "### 2026-01-02 — Second\n\nContent.\n"
    )
    confidence, _, _ = tl.detect(content, FAKE)
    assert confidence == "medium"


def test_timeline_returns_none_for_no_date_headings():
    assert tl.detect("## Regular heading\n\nNo dates here.\n", FAKE) is None


# ---------------------------------------------------------------------------
# detect_shape dispatch
# ---------------------------------------------------------------------------

def test_detect_shape_picks_highest_confidence():
    content = (
        "## Backlog\n\n### Task A\n\n"
        "## In Progress\n\n### Task B\n\n"
        "## Done\n\n### Task C\n"
    )
    match = detect_shape(content, FAKE)
    assert match is not None
    assert match.shape == "kanban"
    assert match.confidence == "high"


def test_detect_shape_returns_none_when_no_pattern():
    match = detect_shape("# Title\n\nJust some regular prose.\n", FAKE)
    assert match is None


def test_detect_shape_includes_suggested_frontmatter():
    content = "## Backlog\n\n### Task A\n\n## Done\n\n### Task B\n"
    match = detect_shape(content, FAKE)
    assert match is not None
    assert match.suggested_frontmatter.get("render-html") == "kanban"


def test_detect_shape_tiebreak_kanban_over_dashboard():
    # kanban: 1 keyword column + 1 card → medium
    # dashboard: 2 typed columns + 2 data rows → medium
    # kanban should win on shape priority
    content = (
        "## Backlog\n\n### Task A\n\n"
        "| Status | Priority |\n"
        "|--------|----------|\n"
        "| Done   | High     |\n"
        "| Open   | Low      |\n"
    )
    match = detect_shape(content, FAKE)
    assert match is not None
    assert match.shape == "kanban"
