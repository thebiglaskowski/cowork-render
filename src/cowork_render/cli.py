"""CLI entry point and dispatch."""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path

import frontmatter

DEFAULT_ROOT = Path("/mnt/c/Users/joela/cowork")
SKIP_DIRS = {".git", ".obsidian", "_archive", "node_modules", ".venv", "__pycache__"}


class NoSignalError(Exception):
    """Source markdown has no render-html: frontmatter — skip silently in bulk mode."""


def companion_path(source: Path) -> Path:
    return source.with_suffix(".html")


def is_stale(source: Path, companion: Path) -> bool:
    if not companion.exists():
        return True
    return source.stat().st_mtime > companion.stat().st_mtime


def dispatch_render(source: Path) -> str:
    post = frontmatter.load(str(source))
    shape = post.metadata.get("render-html")
    if not shape:
        raise NoSignalError(f"no render-html signal in {source}")
    options = post.metadata.get("render-html-options") or {}
    if not re.fullmatch(r"[a-z][a-z0-9_]*", shape):
        raise ImportError(f"invalid shape identifier {shape!r} in {source}")
    try:
        module = importlib.import_module(f"cowork_render.renderers.{shape}")
    except ModuleNotFoundError as exc:
        raise ImportError(f"unknown renderer shape {shape!r} for {source}") from exc
    return module.render(source, options)


def _walk_markdown(root: Path):
    try:
        items = list(root.iterdir())
    except PermissionError as exc:
        print(f"warning: skipping unreadable dir {root} — {exc}", file=sys.stderr)
        return
    for item in items:
        if item.is_symlink():
            continue
        if item.is_dir():
            if item.name in SKIP_DIRS:
                continue
            yield from _walk_markdown(item)
        elif item.suffix == ".md":
            yield item


def render_one(source: Path) -> int:
    try:
        html_content = dispatch_render(source)
        out = companion_path(source)
        out.write_text(html_content, encoding="utf-8")
        print(f"rendered: {source} → {out}")
        return 0
    except Exception as exc:
        print(f"error: {source} — {exc}", file=sys.stderr)
        return 1


def render_walk(root: Path, only_stale: bool) -> int:
    rendered = skipped = errors = 0
    for source in _walk_markdown(root):
        companion = companion_path(source)
        try:
            if only_stale and not is_stale(source, companion):
                skipped += 1
                continue
            html_content = dispatch_render(source)
            companion.write_text(html_content, encoding="utf-8")
            print(f"rendered: {source} → {companion}")
            rendered += 1
        except NoSignalError:
            skipped += 1
        except Exception as exc:
            print(f"error: {source} — {type(exc).__name__}: {exc}", file=sys.stderr)
            errors += 1
    mode = "--stale" if only_stale else "--all"
    print(f"cowork-render {mode}: rendered {rendered}, skipped {skipped}, errors {errors}")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cowork-render",
        description="Render opt-in markdown files in the cowork corpus into HTML companions.",
    )
    parser.add_argument("path", nargs="?", help="Path to a single markdown file to render")
    parser.add_argument(
        "--all", dest="all", action="store_true",
        help="Render all opt-in files in root unconditionally",
    )
    parser.add_argument(
        "--stale", dest="stale", action="store_true",
        help="Render only files whose HTML companion is missing or older than source",
    )
    parser.add_argument(
        "--root", default=None,
        help=f"Root directory for --all/--stale (default: {DEFAULT_ROOT})",
    )
    args = parser.parse_args()

    if args.all or args.stale:
        if args.path:
            root = Path(args.path)
        elif args.root:
            root = Path(args.root)
        else:
            root = DEFAULT_ROOT
        return render_walk(root, only_stale=bool(args.stale))
    if args.path:
        return render_one(Path(args.path))
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
