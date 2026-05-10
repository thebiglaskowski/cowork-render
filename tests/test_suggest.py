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
    # 3 keyword H2s, each with at least one H3 card
    content = (
        "## Backlog\n\n### Task A\n\ndesc\n\n"
        "## In Progress\n\n### Task B\n\n"
        "## Done\n\n### Task C\n"
    )
    confidence, _, _ = kanban.detect(content, FAKE)
    assert confidence == "high"


def test_kanban_medium_confidence_on_two_keyword_columns_of_five():
    # 5 H2s, 2 keywords (Now, Done), 3 non-keyword — qualifies for medium
    content = (
        "## Now\n\n### Task A\n\n"
        "## Done\n\n### Task B\n\n"
        "## References\n\nSome prose.\n\n"
        "## Notes\n\nMore prose.\n\n"
        "## Glossary\n\nDefinitions.\n"
    )
    confidence, _, _ = kanban.detect(content, FAKE)
    assert confidence == "medium"


def test_kanban_returns_none_when_no_h2():
    assert kanban.detect("# Title\n\n### Card\n", FAKE) is None


def test_kanban_returns_none_when_no_keyword_h2s():
    # 3+ H2s but none match status keywords
    content = "## Overview\n\nProse.\n\n## Details\n\n### Sub\n\n## References\n\nLinks.\n"
    assert kanban.detect(content, FAKE) is None


def test_kanban_returns_none_when_fewer_than_three_h2s():
    # 2 H2s even with keyword match — structural minimum not met
    content = "## Backlog\n\n### Task A\n\n## Done\n\n### Task B\n"
    assert kanban.detect(content, FAKE) is None


def test_kanban_normalises_trailing_count():
    # Trailing "(N)" stripped before keyword matching
    content = (
        "## Done (3)\n\n### Task A\n\n"
        "## Backlog (7)\n\n### Task B\n\n"
        "## In Progress (2)\n\n### Task C\n"
    )
    confidence, _, _ = kanban.detect(content, FAKE)
    assert confidence == "high"


def test_kanban_suggested_columns_included():
    content = (
        "## Now\n\n### Task A\n\n"
        "## Next\n\n### Task B\n\n"
        "## Done\n\n### Task C\n"
    )
    _, _, options = kanban.detect(content, FAKE)
    assert "columns" in options
    assert options["columns"] == ["Now", "Next", "Done"]


# ---------------------------------------------------------------------------
# Brief-specified tuning tests (Phase 9 v1.1)
# ---------------------------------------------------------------------------

def test_kanban_brief_style_doc_returns_none():
    content = (
        "## Goal\n\nWhat we're building.\n\n"
        "## Scope\n\nWhat's in/out.\n\n"
        "## Tests\n\nHow to verify.\n\n"
        "## Acceptance\n\nDone means done.\n\n"
        "## Do NOT\n\nThings to avoid.\n"
    )
    assert kanban.detect(content, FAKE) is None


def test_kanban_skill_style_doc_returns_none():
    content = (
        "## When to Invoke\n\nUse when.\n\n"
        "## What This Skill Does\n\nOverview.\n\n"
        "## Output Format\n\nWhat you get.\n\n"
        "## Worked Example\n\nSample interaction.\n"
    )
    assert kanban.detect(content, FAKE) is None


def test_kanban_plan_style_doc_returns_none():
    content = (
        "## Phase 1\n\n### Task 1\n\n"
        "## Phase 2\n\n### Task 2\n\n"
        "## Phase 3\n\n### Task 3\n\n"
        "## Phase 4\n\n### Task 4\n"
    )
    assert kanban.detect(content, FAKE) is None


def test_kanban_high_preserved_four_keyword_h2s_all_with_cards():
    content = (
        "## Now\n\n### Task A\n\n"
        "## Next\n\n### Task B\n\n"
        "## Later\n\n### Task C\n\n"
        "## Done\n\n### Task D\n"
    )
    confidence, _, _ = kanban.detect(content, FAKE)
    assert confidence == "high"


def test_kanban_medium_on_two_keywords_three_non_keywords():
    content = (
        "## Now\n\n### Task A\n\n"
        "## Done\n\n### Task B\n\n"
        "## Notes\n\nSome notes.\n\n"
        "## References\n\nLinks.\n\n"
        "## Glossary\n\nDefs.\n"
    )
    confidence, rationale, _ = kanban.detect(content, FAKE)
    assert confidence == "medium"
    assert "non-keyword" in rationale


def test_kanban_low_on_one_keyword_of_four():
    content = (
        "## Done\n\n### Task A\n\n"
        "## Overview\n\nProse.\n\n"
        "## Details\n\n### Subsection\n\n"
        "## References\n\nLinks.\n"
    )
    confidence, _, _ = kanban.detect(content, FAKE)
    assert confidence == "low"


def test_kanban_below_threshold_two_h2s_both_keywords():
    content = "## Now\n\n### Task A\n\n## Done\n\n### Task B\n"
    assert kanban.detect(content, FAKE) is None


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
    # 3 keyword H2s, each with a card → kanban high
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
    # 3 keyword H2s, each with a card → kanban
    content = (
        "## Now\n\n### Task A\n\n"
        "## Next\n\n### Task B\n\n"
        "## Done\n\n### Task C\n"
    )
    match = detect_shape(content, FAKE)
    assert match is not None
    assert match.suggested_frontmatter.get("render-html") == "kanban"


def test_detect_shape_tiebreak_kanban_over_dashboard():
    # kanban: 2 keyword H2s out of 5 → medium
    # dashboard: 2 typed columns, 2 data rows → medium
    # kanban wins on shape priority tiebreak
    content = (
        "## Now\n\n### Task A\n\n"
        "## Done\n\n### Task B\n\n"
        "## Notes\n\nProse.\n\n"
        "## References\n\nLinks.\n\n"
        "## Glossary\n\nDefs.\n\n"
        "| Status | Priority |\n"
        "|--------|----------|\n"
        "| Done   | High     |\n"
        "| Open   | Low      |\n"
    )
    match = detect_shape(content, FAKE)
    assert match is not None
    assert match.shape == "kanban"
