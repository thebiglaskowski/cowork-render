"""Write a markdown suggestions report from a list of Match objects."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from cowork_render.suggest.scan import Match

_DEFAULT_AUDITS_SUBDIR = Path("claude-environment/cowork-render/audits")


def default_report_path(root: Path) -> Path:
    today = date.today().strftime("%Y-%m-%d")
    return root / _DEFAULT_AUDITS_SUBDIR / f"{today}-render-suggestions.md"


def write_report(matches: list[Match], root: Path, out_path: Path, scanned: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_build_report(matches, root, scanned), encoding="utf-8")


def _build_report(matches: list[Match], root: Path, scanned: int) -> str:
    today = date.today().strftime("%Y-%m-%d")
    n = len(matches)

    high = sum(1 for m in matches if m.confidence == "high")
    medium = sum(1 for m in matches if m.confidence == "medium")
    low = sum(1 for m in matches if m.confidence == "low")

    fm = {"tags": ["cowork-render-suggest"], "cowork-root": str(root), "generated": today}
    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=True).strip()

    lines: list[str] = [
        "---",
        fm_str,
        "---",
        "",
        f"# cowork-render suggestions — {today}",
        "",
        f"{scanned} files scanned · {n} suggestion{'s' if n != 1 else ''}",
        "",
        "## Summary",
        "",
        "| Confidence | Count |",
        "|------------|-------|",
        f"| high       | {high}     |",
        f"| medium     | {medium}   |",
        f"| low        | {low}      |",
        "",
        "## Suggestions",
        "",
    ]

    if not matches:
        lines.append("_No suggestions — corpus is fully opted in or no patterns detected._")
        lines.append("")
    else:
        sorted_matches = sorted(
            matches,
            key=lambda m: (-_CONFIDENCE_RANK[m.confidence], str(m.source_path)),
        )
        for match in sorted_matches:
            try:
                rel = match.source_path.relative_to(root)
            except ValueError:
                rel = match.source_path

            yaml_block = yaml.dump(
                match.suggested_frontmatter,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=True,
            ).strip()

            lines += [
                f"##### `{rel}`",
                "",
                f"**Shape:** {match.shape} · **Confidence:** {match.confidence}",
                "",
                match.rationale,
                "",
                "```yaml",
                yaml_block,
                "```",
                "",
                "- [ ] Accept this suggestion",
                "",
                "---",
                "",
            ]

    return "\n".join(lines)


_CONFIDENCE_RANK: dict[str, int] = {"high": 2, "medium": 1, "low": 0}
