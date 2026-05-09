import subprocess
import sys
import time
from pathlib import Path

import pytest

from cowork_render.cli import NoSignalError, dispatch_render, is_stale

KANBAN_MD = """\
---
render-html: kanban
---

## Now

### A card

Body text.

"""

PLAIN_MD = """\
---
title: plain
---

# Just a doc

No render signal.
"""


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ── dispatch_render ──────────────────────────────────────────────────────────


def test_dispatch_kanban(tmp_path):
    src = _write(tmp_path, "kanban.md", KANBAN_MD)
    result = dispatch_render(src)
    assert result.startswith("<!DOCTYPE html>")


def test_dispatch_no_signal(tmp_path):
    src = _write(tmp_path, "plain.md", PLAIN_MD)
    with pytest.raises(NoSignalError):
        dispatch_render(src)


def test_dispatch_unknown_shape(tmp_path):
    src = _write(tmp_path, "unknown.md", "---\nrender-html: nonexistent\n---\n\n# Hello\n")
    with pytest.raises(ImportError):
        dispatch_render(src)


# ── is_stale ─────────────────────────────────────────────────────────────────


def test_is_stale_companion_missing(tmp_path):
    src = _write(tmp_path, "src.md", "# hello")
    assert is_stale(src, tmp_path / "src.html") is True


def test_is_stale_companion_newer(tmp_path):
    src = _write(tmp_path, "src.md", "# hello")
    companion = tmp_path / "src.html"
    time.sleep(0.05)
    companion.write_text("<html/>")
    assert is_stale(src, companion) is False


def test_is_stale_companion_older(tmp_path):
    companion = tmp_path / "src.html"
    companion.write_text("<html/>")
    time.sleep(0.05)
    src = _write(tmp_path, "src.md", "# hello")
    assert is_stale(src, companion) is True


# ── walk skip rules ───────────────────────────────────────────────────────────


def test_walk_skips_excluded_dirs(tmp_path):
    from cowork_render.cli import _walk_markdown

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config.md").write_text("# git")
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "settings.md").write_text("# obs")
    archive = tmp_path / "_archive" / "sub"
    archive.mkdir(parents=True)
    (archive / "old.md").write_text("# old")
    normal = tmp_path / "notes"
    normal.mkdir()
    (normal / "real.md").write_text("# real")

    found = list(_walk_markdown(tmp_path))
    assert len(found) == 1
    assert found[0].name == "real.md"


# ── CLI invocation ────────────────────────────────────────────────────────────

CLI = [sys.executable, "-m", "cowork_render.cli"]


def test_cli_single_file(tmp_path):
    src = _write(tmp_path, "kanban.md", KANBAN_MD)
    result = subprocess.run(CLI + [str(src)], capture_output=True, text=True)
    assert result.returncode == 0
    companion = tmp_path / "kanban.html"
    assert companion.exists()
    assert companion.read_text().startswith("<!DOCTYPE html>")


def test_cli_single_file_no_signal(tmp_path):
    src = _write(tmp_path, "plain.md", PLAIN_MD)
    result = subprocess.run(CLI + [str(src)], capture_output=True, text=True)
    assert result.returncode != 0
    assert not (tmp_path / "plain.html").exists()
    assert str(src) in result.stderr


def test_cli_all_mode(tmp_path):
    _write(tmp_path, "a.md", KANBAN_MD)
    _write(tmp_path, "b.md", KANBAN_MD)
    _write(tmp_path, "plain.md", PLAIN_MD)
    result = subprocess.run(CLI + ["--all", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert (tmp_path / "a.html").exists()
    assert (tmp_path / "b.html").exists()
    assert not (tmp_path / "plain.html").exists()
    assert "rendered 2" in result.stdout
    assert "skipped 1" in result.stdout


def test_cli_stale_second_run_is_noop(tmp_path):
    _write(tmp_path, "a.md", KANBAN_MD)
    subprocess.run(CLI + ["--stale", str(tmp_path)], capture_output=True, text=True)
    result2 = subprocess.run(CLI + ["--stale", str(tmp_path)], capture_output=True, text=True)
    assert "rendered 0" in result2.stdout


def test_cli_stale_rerenders_touched_source(tmp_path):
    src = _write(tmp_path, "a.md", KANBAN_MD)
    subprocess.run(CLI + ["--stale", str(tmp_path)], capture_output=True, text=True)
    time.sleep(0.05)
    src.write_text(KANBAN_MD)  # update mtime
    result2 = subprocess.run(CLI + ["--stale", str(tmp_path)], capture_output=True, text=True)
    assert "rendered 1" in result2.stdout
