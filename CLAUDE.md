# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync --group dev          # install deps (first time or after pyproject.toml changes)
uv run pytest                # full test suite
uv run pytest tests/test_timeline.py::test_render_produces_valid_html -v  # single test
uv run ruff check src/ tests/  # lint
uv run cowork-render path/to/file.md          # render one file
uv run cowork-render --stale                   # regenerate only outdated HTML companions
uv run cowork-render --all                     # force-regenerate everything
uv run cowork-render --suggest                 # scan corpus for untagged candidates
uv run cowork-render --suggest --shape kanban  # limit to one shape
uv run cowork-render --apply path/to/report.md # write accepted frontmatter back to sources
```

The default corpus root is `/mnt/c/Users/joela/cowork` (hardcoded in `cli.py:DEFAULT_ROOT`). Pass `--root` to override.

## Architecture

### The opt-in signal and dispatch

A markdown file opts into rendering by including `render-html: <shape>` in its YAML frontmatter. The CLI reads this with `python-frontmatter`, then dynamically imports `cowork_render.renderers.<shape>` and calls `module.render(source_path, options)`. Adding a new renderer shape is just adding `renderers/newshape.py` with a `render(source_path, options) -> str` function — no registry to update.

Optional tuning lives under `render-html-options:` in the same frontmatter block; the renderer receives it merged with any CLI-level overrides.

### Renderer contract

Every renderer in `renderers/` exposes two public functions:
- `parse(source_path, options) -> <ShapeDataclass>` — reads and parses the markdown into a structured object
- `render(source_path, options) -> str` — calls `parse`, then `_render_html`, returns a complete self-contained HTML string

The companion file lands next to the source: `foo.md → foo.html`. Nothing in the renderer needs to know about the output path.

### Theme pipeline — never hardcode colors or sizes

Visual tokens live in `DESIGN.md` (YAML frontmatter block). `theme.py` loads that file at import time, walks the `colors:`, `typography:`, `rounded:`, and `spacing:` sections, and emits them as CSS custom properties in a `:root {}` block via `get_theme_css()`. Every renderer inlines that CSS string at the top of its `<style>` block.

Consequence: **renderer CSS must use `var(--token-name)` not hex values or px literals** for any token that exists in DESIGN.md. The contrast test in `tests/test_contrast.py` enforces WCAG AA (4.5:1) on every text/background pair enumerated by `theme.all_text_on_bg_pairs()`.

Current token namespaces: `--bg-*`, `--text-*`, `--border-*`, `--severity-*`, `--link*`, `--font-*`, `--rounded-*`, `--spacing-*`.

### Markdown rendering layer

`_markdown.py` is the single rendering path — **`renderers/_inline.py` is retired and deleted**. Two functions:
- `render_inline(text)` — markdown-it-py "zero" preset with emphasis, code spans, links, and linkify enabled. No block elements, no paragraph wrapper. Use for short field values and table cell content.
- `render_block(text)` — markdown-it-py "commonmark" preset with linkify enabled, HTML passthrough disabled. Full block markdown: paragraphs, lists, headings, fenced code. Every `<pre><code>` block gets wrapped in `.code-block-wrapper` with a `.code-copy-btn` copy button. Use for preamble, section notes, and prose bodies.

The copy-button JS handler is returned by `get_copy_button_js()` and must be injected into each renderer's `<script>` block.

### The suggest/detect system

`--suggest` walks the corpus, skips files that already have `render-html:` frontmatter, and runs each file through the detector pipeline in `suggest/detectors/`. Each detector implements:

```python
def detect(content: str, source_path: Path) -> tuple[str, str, dict] | None:
    # returns (confidence, rationale, suggested_options) or None
    # confidence is "high" | "medium" | "low"
```

`suggest/scan.py` runs all detectors, picks the highest-confidence winner per file, and filters by `--min-confidence`. `suggest/report.py` writes a markdown triage report. `suggest/apply.py` reads an accepted report and patches `render-html` frontmatter back into source files. To add a new detector, create `suggest/detectors/newshape.py` and register it in `suggest/scan.py:_DETECTORS`.

### Prose context `<pre>` overflow

Prose-context `<pre>` blocks (inside `.preamble`, `.preamble-body`, `.section-notes`, `.commentary-body`, `.subsection-notes`) use `white-space: pre-wrap; word-wrap: break-word; max-width: 100%` so long lines wrap inside their panel. `.code-block-wrapper pre` overrides this back to `white-space: pre` (must appear **after** the prose rules in the CSS string so source order wins — specificity is equal).
