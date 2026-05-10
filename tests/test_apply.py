"""Tests for the suggest apply parser in cowork_render.suggest.apply."""

from pathlib import Path

import frontmatter as fm_lib
import pytest

from cowork_render.suggest.apply import ApplyTarget, apply_targets, parse_report


def _write_report(path: Path, root: Path, sections: list[tuple[str, bool, str]]) -> None:
    """Write a suggestions report. sections = [(rel_path, accepted, yaml_block), ...]"""
    lines = [
        "---",
        f"cowork-root: {root}",
        "generated: 2026-05-10",
        "tags:",
        "- cowork-render-suggest",
        "---",
        "",
        "# cowork-render suggestions — 2026-05-10",
        "",
        "## Suggestions",
        "",
    ]
    for rel_path, accepted, yaml_block in sections:
        check = "x" if accepted else " "
        lines += [
            f"##### `{rel_path}`",
            "",
            "**Shape:** kanban · **Confidence:** high",
            "",
            "rationale",
            "",
            "```yaml",
            yaml_block,
            "```",
            "",
            f"- [{check}] Accept this suggestion",
            "",
            "---",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


@pytest.fixture
def corpus(tmp_path: Path):
    source = tmp_path / "some" / "file.md"
    source.parent.mkdir(parents=True)
    source.write_text("# My Board\n\n## Backlog\n\n### Task A\n", encoding="utf-8")
    return tmp_path, source


def test_parse_report_accepted_returns_target(corpus):
    root, source = corpus
    report = root / "report.md"
    _write_report(report, root, [("some/file.md", True, "render-html: kanban")])
    _, targets = parse_report(report)
    assert len(targets) == 1
    assert targets[0].source_path == source


def test_parse_report_unchecked_returns_empty(corpus):
    root, _ = corpus
    report = root / "report.md"
    _write_report(report, root, [("some/file.md", False, "render-html: kanban")])
    _, targets = parse_report(report)
    assert targets == []


def test_parse_report_mixed_returns_only_accepted(corpus):
    root, source = corpus
    source2 = root / "other.md"
    source2.write_text("# Other\n", encoding="utf-8")
    report = root / "report.md"
    _write_report(report, root, [
        ("some/file.md", True, "render-html: kanban"),
        ("other.md", False, "render-html: timeline"),
    ])
    _, targets = parse_report(report)
    assert len(targets) == 1
    assert targets[0].source_path == source


def test_parse_report_raises_on_missing_cowork_root(tmp_path):
    report = tmp_path / "report.md"
    report.write_text(
        "---\ntags: [cowork-render-suggest]\n---\n\n# No cowork-root\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="cowork-root"):
        parse_report(report)


def test_apply_writes_frontmatter(corpus):
    _, source = corpus
    target = ApplyTarget(
        source_path=source,
        frontmatter_patch={"render-html": "kanban", "render-html-options": {"title": "File"}},
    )
    apply_targets([target])
    post = fm_lib.load(str(source))
    assert post.metadata.get("render-html") == "kanban"
    assert post.metadata.get("render-html-options") == {"title": "File"}


def test_apply_skips_existing_without_force(corpus):
    _, source = corpus
    source.write_text("---\nrender-html: dashboard\n---\n\n# Content\n", encoding="utf-8")
    target = ApplyTarget(source_path=source, frontmatter_patch={"render-html": "kanban"})
    applied, skipped, errors = apply_targets([target], force=False)
    assert applied == 0
    assert skipped == 1
    assert fm_lib.load(str(source)).metadata.get("render-html") == "dashboard"


def test_apply_force_overwrites(corpus):
    _, source = corpus
    source.write_text("---\nrender-html: dashboard\n---\n\n# Content\n", encoding="utf-8")
    target = ApplyTarget(source_path=source, frontmatter_patch={"render-html": "kanban"})
    applied, skipped, errors = apply_targets([target], force=True)
    assert applied == 1
    assert fm_lib.load(str(source)).metadata.get("render-html") == "kanban"


def test_apply_dry_run_does_not_write(corpus):
    _, source = corpus
    original = source.read_text(encoding="utf-8")
    target = ApplyTarget(source_path=source, frontmatter_patch={"render-html": "kanban"})
    apply_targets([target], dry_run=True)
    assert source.read_text(encoding="utf-8") == original


def test_apply_idempotent_skips_when_already_matches(corpus):
    _, source = corpus
    source.write_text(
        "---\nrender-html: kanban\nrender-html-options:\n  title: File\n---\n\n# Board\n",
        encoding="utf-8",
    )
    target = ApplyTarget(
        source_path=source,
        frontmatter_patch={"render-html": "kanban", "render-html-options": {"title": "File"}},
    )
    applied, skipped, errors = apply_targets([target])
    assert skipped == 1
    assert applied == 0


def test_apply_file_not_found_counts_as_error(tmp_path):
    target = ApplyTarget(
        source_path=tmp_path / "nonexistent.md",
        frontmatter_patch={"render-html": "kanban"},
    )
    applied, skipped, errors = apply_targets([target])
    assert errors == 1
    assert applied == 0


def test_apply_preserves_existing_frontmatter(corpus):
    _, source = corpus
    source.write_text(
        "---\ntitle: My Board\nauthor: Joe\n---\n\n## Backlog\n\n### Task A\n",
        encoding="utf-8",
    )
    target = ApplyTarget(source_path=source, frontmatter_patch={"render-html": "kanban"})
    apply_targets([target])
    post = fm_lib.load(str(source))
    assert post.metadata.get("title") == "My Board"
    assert post.metadata.get("author") == "Joe"
    assert post.metadata.get("render-html") == "kanban"
