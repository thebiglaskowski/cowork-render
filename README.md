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
