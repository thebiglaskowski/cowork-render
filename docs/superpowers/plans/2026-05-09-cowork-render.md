# cowork-render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a WSL CLI tool that renders opt-in markdown files into rich HTML companions via a `render-html: <shape>` frontmatter signal, shipping as three focused commits across Phase 1 (scaffold), Phase 2 (kanban renderer), and Phase 3 (CLI + dispatch).

**Architecture:** Opt-in via frontmatter signal → shape registry via dynamic import → self-contained HTML output written alongside source. Each renderer shape is an independent module exporting `render(source_path, options) -> str`; the CLI dispatcher imports them by name, so new shapes require zero changes to the orchestration layer.

**Tech Stack:** Python 3.11+, `python-frontmatter`, `hatchling` build backend, `uv` for env management, `pytest` + `ruff` for dev tooling. No JS framework, no templating library — stdlib f-strings + `html.escape` for HTML generation, HTML5 native drag-and-drop.

---

## File map

```
cowork-render/
├── pyproject.toml                              create (Phase 1)
├── README.md                                   create (Phase 1)
├── LICENSE                                     create (Phase 1)
├── .gitignore                                  create (Phase 1)
├── src/
│   └── cowork_render/
│       ├── __init__.py                         create (Phase 1)
│       ├── cli.py                              create stub (Phase 1), replace (Phase 3)
│       └── renderers/
│           ├── __init__.py                     create (Phase 1)
│           └── kanban.py                       create (Phase 2)
└── tests/
    ├── __init__.py                             create (Phase 1)
    ├── test_kanban.py                          create (Phase 2)
    └── test_cli.py                             create (Phase 3)
```

---

## Phase 1 — Scaffold

### Task 1: Create project root files

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `LICENSE`
- Create: `.gitignore`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cowork-render"
version = "0.1.0"
description = "Render selected cowork markdown files into HTML companions per opt-in frontmatter signal"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [{ name = "Joe Laskowski" }]
dependencies = [
  "python-frontmatter>=1.0",
]

[project.scripts]
cowork-render = "cowork_render.cli:main"

[dependency-groups]
dev = [
  "pytest>=8",
  "ruff>=0.4",
]

[tool.hatch.build.targets.wheel]
packages = ["src/cowork_render"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 2: Write `README.md`**

```markdown
---
pair:
  cowork: claude-environment/cowork-render/plan.md
  wsl: ~/github/cowork-render/
  unc: \\wsl$\Ubuntu\home\joe\github\cowork-render\
  division:
    cowork: planning artifacts, brief reproducibility set, design decisions
    wsl: source code (Python renderers, CLI, dispatch logic), tests, dependencies, install scripts
---

# cowork-render

Renders selected markdown files in the cowork corpus into HTML companions, alongside their source. Markdown stays canonical; HTML is a derived view. Rendering is opt-in per file via a `render-html: <shape>` frontmatter signal — files without that field are skipped entirely. Each shape has its own renderer module producing rich domain-specific HTML, not generic markdown→HTML conversion.

**Canonical plan and design reference:** `cowork/claude-environment/cowork-render/plan.md` — that doc is the single source of truth for design decisions, the frontmatter signal convention, the renderer registry pattern, and phasing. Code-side conventions and runtime usage docs live in this repo.

## Status

Phase 1 (scaffolding) shipped. Phase 2 (kanban renderer) is the next work.

## Layout

```
cowork-render/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── src/
│   └── cowork_render/
│       ├── __init__.py
│       ├── cli.py
│       └── renderers/
│           └── __init__.py
└── tests/
    └── __init__.py
```

## Install

```bash
uv sync --group dev
```

## Related

- Plan + design: `cowork/claude-environment/cowork-render/plan.md`
- Sibling pattern: `cowork/claude-environment/cowork-graph/` (same cowork ↔ WSL split, same uv/pyproject/ruff/pytest stack)
- Architectural rule: `cowork/claude-environment/CLAUDE-global.md` "Generated artifacts may be HTML" rule (added 2026-05-09)
```

- [ ] **Step 3: Write `LICENSE`**

```
MIT License

Copyright (c) 2026 Joe Laskowski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE DEALINGS IN THE SOFTWARE.
```

- [ ] **Step 4: Write `.gitignore`**

```
__pycache__/
*.py[cod]
*$py.class
*.so
build/
dist/
*.egg-info/
.installed.cfg
*.egg
.venv/
venv/
env/
.vscode/
.idea/
*.swp
*.swo
.DS_Store
*.log
.pytest_cache/
.coverage
htmlcov/
```

---

### Task 2: Create Python package skeleton

**Files:**
- Create: `src/cowork_render/__init__.py`
- Create: `src/cowork_render/cli.py`
- Create: `src/cowork_render/renderers/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src/cowork_render/renderers tests
```

- [ ] **Step 2: Write `src/cowork_render/__init__.py`**

```python
"""cowork-render — renders selected cowork markdown files into HTML companions."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Write `src/cowork_render/cli.py`** (Phase 1 stub — replaced in Phase 3)

```python
"""CLI entry point. Real commands land in Phase 3."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "cowork-render CLI — Phase 1 scaffolding only. "
        "Real commands land in Phase 3."
    )
    print(
        "See cowork/claude-environment/cowork-render/plan.md "
        "for the design and roadmap."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write `src/cowork_render/renderers/__init__.py`**

```python
"""Renderer registry.

Each shape lives in its own module under this package and exports
`render(source_path: Path, options: dict) -> str`. The CLI's dispatch
logic (Phase 3) reads `render-html:` from the source markdown's
frontmatter, imports the matching module, calls render(), and writes
the resulting HTML alongside the source.

Phase 2 lands the first renderer (kanban). Subsequent shapes
(dashboard, timeline, comparison-grid, chapter-dashboard, etc.) land
as separate modules per the plan's Phase 5+.
"""
```

- [ ] **Step 5: Write `tests/__init__.py`**

```python
# Placeholder. Real tests land alongside Phase 2 (kanban) and Phase 3 (CLI/dispatch) code.
```

---

### Task 3: Verify scaffold and commit Phase 1

**Files:** no new files — verification only

- [ ] **Step 1: Install the environment**

```bash
uv sync --group dev
```

Expected: resolves dependencies, creates `.venv/`, writes `uv.lock`. No errors.

- [ ] **Step 2: Smoke-test the CLI stub**

```bash
uv run cowork-render
```

Expected output:
```
cowork-render CLI — Phase 1 scaffolding only. Real commands land in Phase 3.
See cowork/claude-environment/cowork-render/plan.md for the design and roadmap.
```
Exit code 0.

- [ ] **Step 3: Commit Phase 1**

```bash
git add pyproject.toml README.md LICENSE .gitignore src/ tests/ uv.lock
git commit -m "scaffold cowork-render (Phase 1 deliverable)"
```

---

## Phase 2 — Kanban renderer

### Task 4: Write parse tests (failing)

**Files:**
- Create: `tests/test_kanban.py`

- [ ] **Step 1: Write `tests/test_kanban.py`** with parse tests

```python
import re
from pathlib import Path

import pytest

from cowork_render.renderers import kanban

FIXTURE_MD = """\
---
render-html: kanban
render-html-options:
  title: Test Board
---

# Test Board Title

## Now

### Card A

Body A.

### Card B

Body B.

## Next

### Card C

Body C.

## Later

"""


def _write(tmp_path: Path, content: str, name: str = "test.md") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_parse_fixture(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    board = kanban.parse(path)
    assert len(board.columns) == 3
    assert board.columns[0].name == "Now"
    assert len(board.columns[0].cards) == 2
    assert board.columns[0].cards[0].title == "Card A"
    assert board.columns[0].cards[0].body == "Body A."
    assert board.columns[1].name == "Next"
    assert len(board.columns[1].cards) == 1
    assert board.columns[1].cards[0].title == "Card C"
    assert board.columns[2].name == "Later"
    assert len(board.columns[2].cards) == 0


def test_parse_missing_signal(tmp_path):
    path = _write(tmp_path, "---\ntitle: no signal\n---\n\n# Hello\n")
    with pytest.raises(ValueError, match=str(path)):
        kanban.parse(path)


def test_parse_wrong_signal(tmp_path):
    path = _write(tmp_path, "---\nrender-html: dashboard\n---\n\n# Hello\n")
    with pytest.raises(ValueError, match="kanban"):
        kanban.parse(path)


def test_render_produces_valid_html(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    result = kanban.render(path)
    assert result.startswith("<!DOCTYPE html>")
    assert "Now" in result
    assert "Next" in result
    assert "Card A" in result
    assert "Card B" in result
    assert "Card C" in result


def test_render_escapes_html(tmp_path):
    content = (
        "---\nrender-html: kanban\n---\n\n"
        "## Now\n\n### Safe card\n\n<script>alert(1)</script>\n\n"
    )
    path = _write(tmp_path, content)
    result = kanban.render(path)
    # everything before the embedded JS <script> block
    body_section = result.split("<script>")[0]
    assert "&lt;script&gt;" in body_section
    assert "<script>alert(1)</script>" not in body_section


def test_render_idempotent(tmp_path):
    path = _write(tmp_path, FIXTURE_MD)
    r1 = kanban.render(path)
    r2 = kanban.render(path)

    def normalize(s: str) -> str:
        s = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "UUID", s)
        s = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", "DATE", s)
        return s

    assert normalize(r1) == normalize(r2)


def test_parse_column_ordering_with_options(tmp_path):
    content = """\
---
render-html: kanban
render-html-options:
  columns: [Now, Next, Later, Cut]
---

## Cut

### Cut card

## Now

### Now card

## Later

### Later card

## Next

### Next card

"""
    path = _write(tmp_path, content)
    board = kanban.parse(path)
    assert [c.name for c in board.columns] == ["Now", "Next", "Later", "Cut"]
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_kanban.py -v
```

Expected: 7 errors — `ImportError: cannot import name 'kanban' from 'cowork_render.renderers'` (module doesn't exist yet).

---

### Task 5: Implement `parse()` and data classes

**Files:**
- Create: `src/cowork_render/renderers/kanban.py` (parse functions and dataclasses only — no HTML yet)

- [ ] **Step 1: Write `src/cowork_render/renderers/kanban.py`** (parse half)

```python
"""Kanban renderer — produces drag-and-drop HTML from markdown with H2 columns and H3 cards."""

from __future__ import annotations

import html
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import frontmatter


@dataclass
class Card:
    title: str
    body: str
    card_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Column:
    name: str
    cards: list[Card] = field(default_factory=list)


@dataclass
class Board:
    title: str
    source_path: Path
    columns: list[Column]
    raw_frontmatter: str
    raw_preamble: str


def parse(source_path: Path) -> Board:
    raw_text = source_path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw_text)

    shape = post.metadata.get("render-html")
    if shape is None:
        raise ValueError(f"{source_path}: missing 'render-html' frontmatter signal")
    if shape != "kanban":
        raise ValueError(f"{source_path}: expected render-html: kanban, got: {shape!r}")

    options = post.metadata.get("render-html-options") or {}
    allowed_columns: list[str] | None = options.get("columns") if options else None
    title: str = (options.get("title") if options else None) or source_path.stem

    # Extract raw frontmatter text (between the opening and closing ---)
    raw_frontmatter = ""
    if raw_text.startswith("---"):
        end = raw_text.index("---", 3)
        raw_frontmatter = raw_text[3:end].strip()

    lines = post.content.splitlines()
    preamble_lines: list[str] = []
    columns: list[Column] = []
    current_column: Column | None = None
    current_card_title: str | None = None
    current_card_body: list[str] = []

    def flush_card() -> None:
        nonlocal current_card_title, current_card_body
        if current_card_title is not None and current_column is not None:
            body = "\n".join(current_card_body).strip()
            current_column.cards.append(Card(title=current_card_title, body=body))
        current_card_title = None
        current_card_body = []

    for line in lines:
        h2 = re.match(r"^## (.+)$", line)
        h3 = re.match(r"^### (.+)$", line)
        if h2:
            flush_card()
            col_name = h2.group(1).strip()
            if allowed_columns is None or col_name in allowed_columns:
                current_column = Column(name=col_name)
                columns.append(current_column)
            else:
                current_column = None
        elif h3:
            flush_card()
            current_card_title = h3.group(1).strip()
        elif current_column is None and not columns:
            preamble_lines.append(line)
        elif current_card_title is not None:
            current_card_body.append(line)

    flush_card()

    if allowed_columns:
        col_map = {c.name: c for c in columns}
        columns = [col_map[name] for name in allowed_columns if name in col_map]

    return Board(
        title=title,
        source_path=source_path,
        columns=columns,
        raw_frontmatter=raw_frontmatter,
        raw_preamble="\n".join(preamble_lines).strip(),
    )


def render(source_path: Path, options: dict | None = None) -> str:
    board = parse(source_path)
    return _render_html(board)


def _render_html(board: Board) -> str:
    raise NotImplementedError("Phase 2 step 2 — implement in Task 7")
```

- [ ] **Step 2: Run parse tests**

```bash
uv run pytest tests/test_kanban.py::test_parse_fixture tests/test_kanban.py::test_parse_missing_signal tests/test_kanban.py::test_parse_wrong_signal tests/test_kanban.py::test_parse_column_ordering_with_options -v
```

Expected: 4 PASSED.

- [ ] **Step 3: Confirm render tests still fail**

```bash
uv run pytest tests/test_kanban.py -v
```

Expected: 4 PASSED, 3 FAILED (the render tests hit `NotImplementedError`).

---

### Task 6: Write render tests (already written in Task 4)

The four render tests (`test_render_produces_valid_html`, `test_render_escapes_html`, `test_render_idempotent`) were written in Task 4 and are already failing correctly. No new file changes needed — proceed to Task 7.

---

### Task 7: Implement `_render_html()` — complete the kanban renderer

**Files:**
- Modify: `src/cowork_render/renderers/kanban.py` — replace `_render_html` stub with full implementation

- [ ] **Step 1: Add module-level CSS constant** — replace the `_render_html` stub with the full implementation below. The complete final file is:

```python
"""Kanban renderer — produces drag-and-drop HTML from markdown with H2 columns and H3 cards."""

from __future__ import annotations

import html
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import frontmatter


@dataclass
class Card:
    title: str
    body: str
    card_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Column:
    name: str
    cards: list[Card] = field(default_factory=list)


@dataclass
class Board:
    title: str
    source_path: Path
    columns: list[Column]
    raw_frontmatter: str
    raw_preamble: str


_CSS = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #16161a; color: #e1e4e8; font-family: Georgia, 'Times New Roman', serif; min-height: 100vh; }
.container { max-width: 1400px; margin: 0 auto; padding: 1.5rem; }
header { margin-bottom: 1.5rem; }
header h1 { font-size: 1.6rem; color: #f0f3f6; margin-bottom: 0.4rem; }
.meta { font-size: 0.8rem; color: #8b949e; font-family: 'SF Mono', Menlo, Consolas, monospace; margin-bottom: 0.75rem; }
.actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.btn { padding: 0.4rem 0.9rem; border-radius: 4px; border: none; cursor: pointer; font-size: 0.85rem; font-family: inherit; }
.btn-primary { background: #58a6ff; color: #fff; }
.btn-primary:hover { background: #79b8ff; }
.btn-secondary { background: #25272e; color: #e1e4e8; border: 1px solid #2d3138; }
.btn-secondary:hover { background: #2a2c33; }
.board { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; align-items: start; }
.column { background: #1f2128; border: 1px solid #2d3138; border-radius: 6px; padding: 0.75rem; }
.column-title { font-size: 1rem; color: #f0f3f6; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center; }
.card-count { background: #25272e; border: 1px solid #2d3138; border-radius: 10px; font-size: 0.75rem; padding: 0.1rem 0.5rem; color: #8b949e; }
.cards { display: flex; flex-direction: column; gap: 0.5rem; min-height: 40px; padding: 4px; }
.cards.drop-active { outline: 2px dashed #58a6ff; background: #1c2030; border-radius: 4px; }
.card { background: #25272e; border: 1px solid #2d3138; border-radius: 5px; padding: 0.6rem 0.75rem; cursor: grab; }
.card:hover { background: #2a2c33; }
.card.dragging { opacity: 0.5; cursor: grabbing; }
.card-title { font-size: 0.9rem; color: #f0f3f6; font-weight: normal; }
.card-body { font-size: 0.8rem; color: #8b949e; margin-top: 0.25rem; line-height: 1.4; }
.no-cards { color: #8b949e; font-size: 0.8rem; font-style: italic; text-align: center; padding: 0.5rem 0; }
footer { margin-top: 1.5rem; font-size: 0.75rem; color: #8b949e; font-family: 'SF Mono', Menlo, Consolas, monospace; }
#export-fallback { width: 100%; margin-top: 0.5rem; background: #1f2128; color: #e1e4e8; border: 1px solid #2d3138; padding: 0.5rem; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.8rem; height: 200px; }
@media (max-width: 600px) { .board { grid-template-columns: 1fr; } }"""

# Plain string (not f-string) — JS braces don't need escaping.
# __FM_JSON__ and __PREAMBLE_JSON__ are replaced at render time.
_JS_TEMPLATE = """\
const RAW_FRONTMATTER = __FM_JSON__;
const RAW_PREAMBLE = __PREAMBLE_JSON__;

let draggedCard = null;

document.querySelectorAll('.card').forEach(card => {
  card.addEventListener('dragstart', e => {
    draggedCard = card;
    card.classList.add('dragging');
    e.dataTransfer.setData('text/plain', card.dataset.cardId);
    e.dataTransfer.effectAllowed = 'move';
  });
  card.addEventListener('dragend', () => {
    card.classList.remove('dragging');
    draggedCard = null;
    document.querySelectorAll('.cards').forEach(c => c.classList.remove('drop-active'));
  });
});

document.querySelectorAll('.cards').forEach(zone => {
  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('drop-active');
  });
  zone.addEventListener('dragleave', e => {
    if (!zone.contains(e.relatedTarget)) zone.classList.remove('drop-active');
  });
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drop-active');
    if (draggedCard) {
      zone.appendChild(draggedCard);
      updateCardCounts();
    }
  });
});

function updateCardCounts() {
  document.querySelectorAll('.column').forEach(col => {
    const count = col.querySelectorAll('.card').length;
    col.querySelector('.card-count').textContent = count;
  });
}

document.getElementById('copy-md').addEventListener('click', () => {
  const lines = ['---', RAW_FRONTMATTER, '---'];
  if (RAW_PREAMBLE) { lines.push(''); lines.push(RAW_PREAMBLE); }
  document.querySelectorAll('.column').forEach(col => {
    lines.push('');
    lines.push('## ' + col.dataset.column);
    col.querySelectorAll('.card').forEach(card => {
      lines.push('');
      lines.push('### ' + card.querySelector('.card-title').textContent.trim());
      const body = card.querySelector('.card-body');
      if (body) { lines.push(''); lines.push(body.textContent.trim()); }
    });
  });
  const md = lines.join('\\n');
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(md).then(() => {
      const btn = document.getElementById('copy-md');
      const orig = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => btn.textContent = orig, 1500);
    });
  } else {
    const ta = document.getElementById('export-fallback');
    ta.hidden = false;
    ta.value = md;
    ta.select();
  }
});

document.getElementById('reset').addEventListener('click', () => window.location.reload());"""


def parse(source_path: Path) -> Board:
    raw_text = source_path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw_text)

    shape = post.metadata.get("render-html")
    if shape is None:
        raise ValueError(f"{source_path}: missing 'render-html' frontmatter signal")
    if shape != "kanban":
        raise ValueError(f"{source_path}: expected render-html: kanban, got: {shape!r}")

    options = post.metadata.get("render-html-options") or {}
    allowed_columns: list[str] | None = options.get("columns") if options else None
    title: str = (options.get("title") if options else None) or source_path.stem

    raw_frontmatter = ""
    if raw_text.startswith("---"):
        end = raw_text.index("---", 3)
        raw_frontmatter = raw_text[3:end].strip()

    lines = post.content.splitlines()
    preamble_lines: list[str] = []
    columns: list[Column] = []
    current_column: Column | None = None
    current_card_title: str | None = None
    current_card_body: list[str] = []

    def flush_card() -> None:
        nonlocal current_card_title, current_card_body
        if current_card_title is not None and current_column is not None:
            body = "\n".join(current_card_body).strip()
            current_column.cards.append(Card(title=current_card_title, body=body))
        current_card_title = None
        current_card_body = []

    for line in lines:
        h2 = re.match(r"^## (.+)$", line)
        h3 = re.match(r"^### (.+)$", line)
        if h2:
            flush_card()
            col_name = h2.group(1).strip()
            if allowed_columns is None or col_name in allowed_columns:
                current_column = Column(name=col_name)
                columns.append(current_column)
            else:
                current_column = None
        elif h3:
            flush_card()
            current_card_title = h3.group(1).strip()
        elif current_column is None and not columns:
            preamble_lines.append(line)
        elif current_card_title is not None:
            current_card_body.append(line)

    flush_card()

    if allowed_columns:
        col_map = {c.name: c for c in columns}
        columns = [col_map[name] for name in allowed_columns if name in col_map]

    return Board(
        title=title,
        source_path=source_path,
        columns=columns,
        raw_frontmatter=raw_frontmatter,
        raw_preamble="\n".join(preamble_lines).strip(),
    )


def render(source_path: Path, options: dict | None = None) -> str:
    board = parse(source_path)
    return _render_html(board)


def _render_html(board: Board) -> str:
    render_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fm_json = json.dumps(board.raw_frontmatter)
    preamble_json = json.dumps(board.raw_preamble)
    js = _JS_TEMPLATE.replace("__FM_JSON__", fm_json).replace("__PREAMBLE_JSON__", preamble_json)
    cols = _render_columns(board.columns)
    title_esc = html.escape(board.title)
    source_esc = html.escape(str(board.source_path))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_esc}</title>
  <style>{_CSS}</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>{title_esc}</h1>
      <div class="meta">{source_esc} &middot; rendered {render_date}</div>
      <div class="actions">
        <button id="copy-md" class="btn btn-primary">Copy as markdown</button>
        <button id="reset" class="btn btn-secondary">Reset to source order</button>
      </div>
    </header>
    <main class="board">
{cols}
    </main>
    <footer>generated by cowork-render kanban v1 &middot; {render_date}</footer>
    <textarea id="export-fallback" hidden></textarea>
  </div>
  <script>{js}</script>
</body>
</html>"""


def _render_columns(columns: list[Column]) -> str:
    return "\n".join(_render_column(col) for col in columns)


def _render_column(col: Column) -> str:
    name_esc = html.escape(col.name)
    cards_html = _render_cards(col.cards)
    return (
        f'      <section class="column" data-column="{name_esc}">\n'
        f'        <h2 class="column-title">{name_esc}'
        f' <span class="card-count">{len(col.cards)}</span></h2>\n'
        f'        <div class="cards">{cards_html}\n        </div>\n'
        f"      </section>"
    )


def _render_cards(cards: list[Card]) -> str:
    if not cards:
        return '\n          <p class="no-cards">no cards</p>'
    return "".join(_render_card(card) for card in cards)


def _render_card(card: Card) -> str:
    body = ""
    if card.body:
        body = f'\n            <div class="card-body">{html.escape(card.body)}</div>'
    return (
        f'\n          <article class="card" draggable="true" data-card-id="{card.card_id}">\n'
        f"            <h3 class=\"card-title\">{html.escape(card.title)}</h3>{body}\n"
        f"          </article>"
    )
```

- [ ] **Step 2: Run all kanban tests**

```bash
uv run pytest tests/test_kanban.py -v
```

Expected: 7 PASSED.

---

### Task 8: Lint check and commit Phase 2

- [ ] **Step 1: Run ruff**

```bash
uv run ruff check src/ tests/
```

Expected: no output (clean).

- [ ] **Step 2: Manual smoke test**

```bash
cat > /tmp/test-kanban.md << 'EOF'
---
render-html: kanban
render-html-options:
  title: "Smoke Test Board"
---

## Now

### Build the thing

Make it work.

### Write the tests

Red, green, refactor.

## Next

### Ship it

Deploy.

## Later

### Profit

Eventually.

EOF
python -c "
from pathlib import Path
from cowork_render.renderers import kanban
html = kanban.render(Path('/tmp/test-kanban.md'))
Path('/tmp/test-kanban.html').write_text(html)
print('Written to /tmp/test-kanban.html')
"
```

Open `/tmp/test-kanban.html` in a browser. Verify: four columns present, cards visible, drag-and-drop works between columns, "Copy as markdown" button copies a valid markdown string, no `http://`/`https://` URLs in the file (run `grep -E 'https?://' /tmp/test-kanban.html` — should return nothing).

- [ ] **Step 3: Commit Phase 2**

```bash
git add src/cowork_render/renderers/kanban.py tests/test_kanban.py
git commit -m "add kanban renderer (Phase 2)"
```

---

## Phase 3 — CLI + frontmatter dispatch

### Task 9: Write dispatch and stale tests (failing)

**Files:**
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write `tests/test_cli.py`** with dispatch and stale tests

```python
import subprocess
import sys
import time
from pathlib import Path

import pytest

from cowork_render.cli import NoSignalError, companion_path, dispatch_render, is_stale

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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: errors on import — `ImportError: cannot import name 'NoSignalError' from 'cowork_render.cli'` (functions don't exist in the stub yet).

---

### Task 10: Implement dispatch layer

**Files:**
- Modify: `src/cowork_render/cli.py` — replace Phase 1 stub with dispatch functions

Write the following to `src/cowork_render/cli.py` (this is the partial Phase 3 implementation — `main`, `render_one`, and `render_walk` land in Task 12):

- [ ] **Step 1: Write dispatch functions to `src/cowork_render/cli.py`**

```python
"""CLI entry point and dispatch."""

from __future__ import annotations

import importlib
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
    try:
        module = importlib.import_module(f"cowork_render.renderers.{shape}")
    except ModuleNotFoundError as exc:
        raise ImportError(f"unknown renderer shape {shape!r} for {source}") from exc
    return module.render(source, options)


def _walk_markdown(root: Path):
    for item in root.iterdir():
        if item.is_symlink():
            continue
        if item.is_dir():
            if item.name in SKIP_DIRS:
                continue
            yield from _walk_markdown(item)
        elif item.suffix == ".md":
            yield item


def main() -> int:
    print("cowork-render CLI — dispatch layer landing in Task 12.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run dispatch and stale tests**

```bash
uv run pytest tests/test_cli.py::test_dispatch_kanban tests/test_cli.py::test_dispatch_no_signal tests/test_cli.py::test_dispatch_unknown_shape tests/test_cli.py::test_is_stale_companion_missing tests/test_cli.py::test_is_stale_companion_newer tests/test_cli.py::test_is_stale_companion_older tests/test_cli.py::test_walk_skips_excluded_dirs -v
```

Expected: 7 PASSED.

- [ ] **Step 3: Confirm kanban tests still pass**

```bash
uv run pytest tests/test_kanban.py -v
```

Expected: 7 PASSED.

---

### Task 11: Write walk and CLI tests (already written in Task 9)

The five CLI invocation tests (`test_cli_single_file`, `test_cli_single_file_no_signal`, `test_cli_all_mode`, `test_cli_stale_second_run_is_noop`, `test_cli_stale_rerenders_touched_source`) were written in Task 9 and are already failing. No new file changes needed — proceed to Task 12.

---

### Task 12: Implement `render_one`, `render_walk`, `main()`

**Files:**
- Modify: `src/cowork_render/cli.py` — replace `main()` stub with full CLI

Replace the full `src/cowork_render/cli.py` with the complete implementation:

- [ ] **Step 1: Write the complete `src/cowork_render/cli.py`**

```python
"""CLI entry point and dispatch."""

from __future__ import annotations

import argparse
import importlib
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
    try:
        module = importlib.import_module(f"cowork_render.renderers.{shape}")
    except ModuleNotFoundError as exc:
        raise ImportError(f"unknown renderer shape {shape!r} for {source}") from exc
    return module.render(source, options)


def _walk_markdown(root: Path):
    for item in root.iterdir():
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
            print(f"skipped: {source} — {type(exc).__name__}: {exc}", file=sys.stderr)
            errors += 1
    mode = "--stale" if only_stale else "--all"
    print(f"cowork-render {mode}: rendered {rendered}, skipped {skipped} (no signal), errors {errors}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cowork-render",
        description="Render opt-in markdown files in the cowork corpus into HTML companions.",
    )
    parser.add_argument("path", nargs="?", help="Path to a single markdown file to render")
    parser.add_argument("--all", dest="all", action="store_true",
                        help="Render all opt-in files in root unconditionally")
    parser.add_argument("--stale", dest="stale", action="store_true",
                        help="Render only files whose HTML companion is missing or older than source")
    parser.add_argument("--root", default=None,
                        help=f"Root directory for --all/--stale (default: {DEFAULT_ROOT})")
    args = parser.parse_args()

    if args.path:
        return render_one(Path(args.path))
    if args.all or args.stale:
        root = Path(args.root) if args.root else DEFAULT_ROOT
        return render_walk(root, only_stale=bool(args.stale))
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run all CLI tests**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: 12 PASSED.

- [ ] **Step 3: Run full suite**

```bash
uv run pytest -v
```

Expected: 19 PASSED (7 kanban + 12 CLI).

---

### Task 13: Lint check and commit Phase 3

- [ ] **Step 1: Run ruff**

```bash
uv run ruff check src/ tests/
```

Expected: no output (clean).

- [ ] **Step 2: Verify `--help`**

```bash
uv run cowork-render --help
```

Expected output includes: `<path>`, `--all`, `--stale`, `--root`.

- [ ] **Step 3: Verify back-to-back `--stale` is a no-op**

```bash
uv run cowork-render --stale /tmp/some-empty-dir 2>/dev/null || true
uv run cowork-render --stale /tmp/ 2>/dev/null | grep "rendered 0" && echo "no-op confirmed"
```

- [ ] **Step 4: Commit Phase 3**

```bash
git add src/cowork_render/cli.py tests/test_cli.py
git commit -m "add CLI and frontmatter dispatch (Phase 3)"
```

---

## Done

Three commits land a working v1:

1. `scaffold cowork-render (Phase 1 deliverable)` — project structure, uv env, CLI stub
2. `add kanban renderer (Phase 2)` — kanban.py, test_kanban.py, 7 tests green
3. `add CLI and frontmatter dispatch (Phase 3)` — cli.py, test_cli.py, 19 tests green

After Phase 3: `uv run cowork-render --all /mnt/c/Users/joela/cowork` walks the corpus and renders every file with `render-html:` frontmatter. `uv run cowork-render --stale` re-runs safely as a no-op when nothing is stale.
