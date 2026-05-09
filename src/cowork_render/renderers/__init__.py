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
