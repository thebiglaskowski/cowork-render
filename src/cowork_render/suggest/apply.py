"""Parse a suggestions report and apply accepted frontmatter patches to source files."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

import frontmatter
import yaml

_H5_PATH = re.compile(r"^##### `(.+)`", re.MULTILINE)
_CHECKBOX_ACCEPTED = re.compile(r"-\s+\[x\]\s+Accept this suggestion", re.IGNORECASE)
_YAML_BLOCK = re.compile(r"```yaml\n(.*?)```", re.DOTALL)
_SECTION_END = re.compile(r"^(?:#{2,5}\s|---\s*$)", re.MULTILINE)


class ApplyTarget(NamedTuple):
    source_path: Path
    frontmatter_patch: dict


class _SkipError(Exception):
    pass


def parse_report(report_path: Path) -> tuple[Path, list[ApplyTarget]]:
    """Parse a suggestions report; return (cowork_root, list of accepted targets)."""
    text = report_path.read_text(encoding="utf-8")
    post = frontmatter.loads(text)

    cowork_root_str = post.metadata.get("cowork-root")
    if not cowork_root_str:
        raise ValueError(f"{report_path}: missing 'cowork-root' frontmatter key")
    cowork_root = Path(str(cowork_root_str))

    content = post.content
    targets: list[ApplyTarget] = []

    for h5_m in _H5_PATH.finditer(content):
        rel_path_str = h5_m.group(1)

        section_end = len(content)
        for end_m in _SECTION_END.finditer(content, h5_m.end()):
            section_end = end_m.start()
            break

        section = content[h5_m.start():section_end]

        if not _CHECKBOX_ACCEPTED.search(section):
            continue

        yaml_match = _YAML_BLOCK.search(section)
        if not yaml_match:
            continue

        try:
            patch = yaml.safe_load(yaml_match.group(1))
        except yaml.YAMLError:
            continue

        if not isinstance(patch, dict):
            continue

        targets.append(ApplyTarget(
            source_path=cowork_root / rel_path_str,
            frontmatter_patch=patch,
        ))

    return cowork_root, targets


def apply_targets(
    targets: list[ApplyTarget],
    dry_run: bool = False,
    force: bool = False,
) -> tuple[int, int, int]:
    """Apply accepted suggestions. Returns (applied, skipped, errors)."""
    applied = skipped = errors = 0
    for target in targets:
        try:
            _apply_one(target, dry_run=dry_run, force=force)
            applied += 1
        except _SkipError as exc:
            print(f"skip: {target.source_path} — {exc}")
            skipped += 1
        except Exception as exc:
            print(f"error: {target.source_path} — {exc}", file=sys.stderr)
            errors += 1
    return applied, skipped, errors


def _apply_one(target: ApplyTarget, dry_run: bool, force: bool) -> None:
    path = target.source_path
    if not path.exists():
        raise FileNotFoundError(f"source file not found: {path}")

    text = path.read_text(encoding="utf-8")
    post = frontmatter.loads(text)

    existing_shape = post.metadata.get("render-html")
    if existing_shape and not force:
        raise _SkipError(f"already has render-html: {existing_shape!r} (use --force to overwrite)")

    if existing_shape == target.frontmatter_patch.get("render-html"):
        existing_opts = post.metadata.get("render-html-options") or {}
        new_opts = target.frontmatter_patch.get("render-html-options") or {}
        if existing_opts == new_opts:
            raise _SkipError("already matches suggested frontmatter")

    for key, value in target.frontmatter_patch.items():
        post.metadata[key] = value

    if dry_run:
        print(f"dry-run: would write {path}")
        print(f"  render-html: {target.frontmatter_patch.get('render-html')}")
        return

    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    print(f"applied: {path}")
