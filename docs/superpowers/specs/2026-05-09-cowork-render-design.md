# cowork-render — Design Spec

**Date:** 2026-05-09
**Status:** approved
**Scope:** Phase 1 (scaffold) + Phase 2 (kanban renderer) + Phase 3 (CLI + dispatch)

---

## What this is

A WSL CLI tool that renders selected markdown files in the cowork corpus into HTML companions. Markdown stays canonical; HTML is a derived view. Rendering is opt-in per file via a `render-html: <shape>` frontmatter signal — files without that field are skipped silently. Each shape has its own renderer module producing rich domain-specific HTML, not generic markdown→HTML conversion.

Canonical design reference: `cowork/claude-environment/cowork-render/plan.md`.

---

## Phase 1 — Scaffold

### File structure

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

### Key decisions

- **Build backend:** hatchling (standard, no setup.py complexity)
- **Runtime dep:** `python-frontmatter>=1.0` only — everything else is stdlib
- **Dev deps:** `pytest>=8`, `ruff>=0.4` via `[dependency-groups]`
- **Entry point:** `cowork-render = "cowork_render.cli:main"`
- **Python:** `>=3.11`
- **README.md** carries the reciprocal `pair:` frontmatter block activating the cowork ↔ WSL pairing convention

### Acceptance

- `uv sync --group dev` installs without error
- `uv run cowork-render` prints Phase 1 placeholder and exits 0
- Single commit: `scaffold cowork-render (Phase 1 deliverable)`

---

## Phase 2 — Kanban renderer

### Module: `src/cowork_render/renderers/kanban.py`

**Data model:**

```python
@dataclass
class Card:
    title: str
    body: str
    card_id: str  # uuid4, generated at render time

@dataclass
class Column:
    name: str
    cards: list[Card]

@dataclass
class Board:
    title: str
    source_path: Path
    columns: list[Column]
    raw_frontmatter: str   # preserved verbatim for export round-trip
    raw_preamble: str      # H1 + text before first H2, preserved but not rendered
```

**Public API:**

- `parse(source_path: Path) -> Board` — reads frontmatter via `python-frontmatter`, validates `render-html == 'kanban'` (raises `ValueError` if absent or wrong shape), extracts columns from `## ` H2s, cards from `### ` H3s within each column, applies `render-html-options.columns` filter if present
- `render(source_path: Path, options: dict | None = None) -> str` — calls parse, delegates to `_render_html`
- `_render_html(board: Board) -> str` — builds self-contained HTML via f-strings; every piece of user content through `html.escape`

### HTML output

Self-contained single file — embedded `<style>` and `<script>` blocks, no external URLs, no JS framework.

**Palette (matches cowork-graph audit HTML family):**

| Token | Value |
|-------|-------|
| body bg | `#16161a` |
| surface | `#1f2128` |
| text | `#e1e4e8` |
| muted | `#8b949e` |
| border | `#2d3138` |
| card bg | `#25272e` |
| button primary | `#58a6ff` |
| drop-zone active | `#58a6ff` dashed border, `#1c2030` bg |

**Layout:** CSS Grid `repeat(auto-fit, minmax(220px, 1fr))` — horizontal columns on wide, stacked on mobile (<600px). Each column: title + card-count pill + vertical card list + drop-zone styling.

**Drag-and-drop (HTML5 native):**
- `draggable="true"` on each `<article class="card">` with a `data-card-id` (uuid)
- `dragstart` → store card ID in `dataTransfer`, add `dragging` class
- `dragover` on column `.cards` div → prevent default, add `drop-zone-active`
- `drop` → move card element to target column, update card-count pills
- v1: append-to-end of target column; intra-column reorder deferred

**"Copy as markdown" button:**
Reads current DOM state, reconstructs markdown (original frontmatter + preamble verbatim, columns/cards in current DOM order), writes to clipboard via `navigator.clipboard.writeText()`. Fallback: unhide `<textarea id="export-fallback">` for manual copy.

**"Reset to source order" button:** `window.location.reload()`.

### Tests: `tests/test_kanban.py`

1. Parse fixture — three columns, six cards, correct assignment and ordering
2. Missing frontmatter signal → `ValueError` naming source path
3. Wrong frontmatter signal (`render-html: dashboard`) → `ValueError` with expected vs actual
4. Render returns string starting with `<!DOCTYPE html>`, containing all column names and card titles
5. XSS escape — `<script>alert(1)</script>` in card body → `&lt;script&gt;` in output
6. Idempotency — same Board input produces structurally identical output (modulo UUIDs)
7. Column ordering via `render-html-options.columns` — options order wins over source order

### Acceptance

- `uv run pytest` — all green
- `uv run ruff check src/ tests/` — clean
- Manual test: render a fixture file, open HTML in browser, verify drag-and-drop and clipboard export work
- No `http://`/`https://` URLs in the rendered HTML output
- Single commit: `add kanban renderer (Phase 2)`

---

## Phase 3 — CLI + frontmatter dispatch

### CLI surface

```
cowork-render <path>             # render single file, always, raises on error
cowork-render --all [root]       # walk corpus, render every opt-in file
cowork-render --stale [root]     # walk corpus, render only missing/stale companions
cowork-render --help
```

Default root: `/mnt/c/Users/joela/cowork`

### argparse structure

Top-level flags (not subcommands) — simpler for three modes, cleaner `--help`:
- Positional `path` (optional) for single-file mode
- `--all` flag for bulk unconditional
- `--stale` flag for bulk stale-only
- `--root` option (default `/mnt/c/Users/joela/cowork`) for bulk root override

### Module: `src/cowork_render/cli.py`

**Key functions:**

```python
def main() -> int           # argparse entry point
def render_one(source, strict) -> int
def render_walk(root, only_stale) -> int
def dispatch_render(source) -> str   # reads frontmatter, imports renderer, returns HTML
def companion_path(source) -> Path   # source.with_suffix('.html')
def is_stale(source, companion) -> bool
class NoSignalError(Exception)       # no render-html: field — skip silently
```

**Dispatch logic:**
1. `frontmatter.load(source)` — read metadata
2. `shape = metadata.get("render-html")` — absent → `NoSignalError` (skip)
3. `options = metadata.get("render-html-options", {})`
4. `module = importlib.import_module(f"cowork_render.renderers.{shape}")`
5. `return module.render(source, options)`

New renderer = new module. Zero changes to dispatcher.

**Stale detection:**
```python
def is_stale(source, companion):
    if not companion.exists():
        return True
    return source.stat().st_mtime > companion.stat().st_mtime
```

**Walk skip list:** `.git`, `.obsidian`, `_archive`, `node_modules`, `.venv`, `__pycache__`. Never follow `.projects` symlink. Only `.md` files processed; `.html` companions never re-walked.

**Error handling:**
- Single-file mode: exceptions propagate, exit non-zero
- Bulk modes: log warning to stderr, continue to next file

**Output:**
- Per-file success: `rendered: <source> → <companion>` to stdout
- Per-file skip/error in bulk: to stderr
- End of bulk run summary: `cowork-render --stale: rendered N, skipped N (no signal), errors N`

### Tests: `tests/test_cli.py`

1. Dispatch — kanban fixture → HTML starting with `<!DOCTYPE html>`
2. Dispatch — no signal → `NoSignalError`
3. Dispatch — unknown shape → `ImportError`
4. Stale — companion missing → `True`
5. Stale — companion newer than source → `False`
6. Stale — source newer than companion → `True`
7. Walk skip rules — files in `.git/`, `.obsidian/`, `_archive/` not yielded; normal subdir file is
8. CLI single-file — companion created, exit 0
9. CLI single-file no signal — no companion, exit non-zero, stderr names source
10. CLI `--all` — two opt-in + one plain → two HTML files, summary `rendered 2, skipped 1, errors 0`
11. CLI `--stale` — second run produces zero new files
12. CLI `--stale` — after touching one source, exactly that file regenerated

All Phase 2 tests must stay green.

### Acceptance

- `uv run pytest` — all green (Phase 2 + Phase 3)
- `uv run ruff check src/ tests/` — clean
- `uv run cowork-render --help` shows all three modes
- `uv run cowork-render <kanban-markdown>` produces companion at expected path
- `uv run cowork-render --stale` back-to-back is a no-op the second time
- Single commit: `add CLI and frontmatter dispatch (Phase 3)`
