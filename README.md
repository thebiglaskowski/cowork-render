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

## Install

```bash
uv sync --group dev
```

## Usage

```bash
# Render a single file
uv run cowork-render path/to/file.md

# Regenerate only files whose HTML is older than their source .md
uv run cowork-render --stale

# Force-regenerate all opted-in files
uv run cowork-render --all

# Scan the corpus for untagged files that look like known shapes
uv run cowork-render --suggest

# Limit suggestion scan to one shape
uv run cowork-render --suggest --shape kanban

# Apply accepted suggestions from a triage report back to source files
uv run cowork-render --apply path/to/report.md

# Override the corpus root (default: /mnt/c/Users/joela/cowork)
uv run cowork-render --root /some/other/path --stale
```

## Opting a file in

Add to the file's YAML frontmatter:

```yaml
render-html: dashboard
render-html-options:
  title: My Title      # optional — defaults to filename stem
  subtitle: Subtitle   # optional
```

Supported shapes: `kanban`, `dashboard`, `timeline`.

## Development

```bash
uv run pytest                                              # full test suite
uv run pytest tests/test_timeline.py::test_name -v        # single test
uv run ruff check src/ tests/                             # lint
uv run ruff format src/ tests/                            # format
```

## Adding a renderer

Create `src/cowork_render/renderers/newshape.py` with:

```python
def parse(source_path, options=None): ...   # returns a dataclass
def render(source_path, options=None) -> str: ...  # returns complete HTML string
```

No registry to update — the CLI dispatches by importing `cowork_render.renderers.<shape>` dynamically.

## Architecture notes

- **Theme pipeline:** Visual tokens (colors, typography, spacing) live in `DESIGN.md` frontmatter. `theme.py` loads them at import time and emits CSS custom properties via `get_theme_css()`. Renderer CSS must use `var(--token-name)` — never hardcode hex or px values for tokens that exist in `DESIGN.md`. `get_diagram_css()` similarly provides shared diagram styles.
- **Markdown layer:** `_markdown.py` is the single rendering path. `render_inline()` for short field values, `render_block()` for prose bodies. `render_block` automatically detects ASCII tree/flow diagrams and replaces them with styled HTML structures before applying the code-copy-button wrapper to remaining code blocks.
- **Suggest/detect system:** `suggest/detectors/` holds one detector per shape. Each returns `(confidence, rationale, suggested_options)` or `None`. Register new detectors in `suggest/scan.py`.

## Related

- Plan + design: `cowork/claude-environment/cowork-render/plan.md`
- Sibling pattern: `cowork/claude-environment/cowork-graph/`
