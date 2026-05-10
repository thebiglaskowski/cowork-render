"""Timeline renderer — produces vertical timeline HTML from date-prefixed markdown entries."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

from cowork_render._markdown import get_copy_button_js
from cowork_render.renderers._inline import render_inline_markdown
from cowork_render.theme import get_theme_css

# Matches H2–H4 headings with a YYYY-MM-DD — title date prefix.
# Compatible with cowork-graph's decision-heading pattern.
RE_ENTRY_HEADING = re.compile(
    r'^(?P<level>#{2,4})\s+(?P<date>\d{4}-\d{2}-\d{2})\s+—\s+(?P<title>.+?)\s*$',
    re.MULTILINE,
)

# Extracts bold-prefix fields: **Field Name:** value ... up to next field, heading, or end.
RE_FIELD = re.compile(
    r'^\*\*(?P<field>[A-Z][^*:]+?):\*\*\s*(?P<value>.*?)(?=^\*\*[A-Z][^*:]+?:\*\*|^#{2,4}\s|\Z)',
    re.MULTILINE | re.DOTALL,
)

_TAG_SPLIT = re.compile(r'[,;+]|\s+&\s+')


@dataclass
class Field:
    name: str
    value_md: str


@dataclass
class Entry:
    date: str
    title: str
    fields: list[Field] = field(default_factory=list)
    prose_md: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Timeline:
    title: str
    subtitle: str
    source_path: Path
    preamble_md: str
    entries: list[Entry]


_CSS = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg-base); color: var(--text-base); font-family: Georgia, 'Times New Roman', serif; font-size: var(--font-body-font-size); line-height: var(--font-body-line-height); min-height: 100vh; }
.container { max-width: 1100px; margin: 0 auto; padding: 1.5rem; }
header { margin-bottom: 1.75rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-subtle); position: relative; }
header::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 80px; height: 2px; background: linear-gradient(90deg, var(--link), var(--severity-ok)); border-radius: 999px; }
header h1 { font-size: 1.6rem; color: var(--text-heading); margin-bottom: 0.25rem; }
.subtitle { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.4rem; }
.meta { font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono-font-family); }
.preamble { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--rounded-lg); padding: 0.75rem 1rem; margin-bottom: 1.25rem; box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 1px 2px rgba(0,0,0,0.4), 0 4px 8px rgba(0,0,0,0.15); }
.preamble summary { color: var(--text-heading); cursor: pointer; font-size: 0.9rem; user-select: none; }
.preamble-body { margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-muted); line-height: 1.55; }
.preamble-body p { margin: 0; }
.preamble-body p + p { margin-top: 0.55rem; }
.filter-bar { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; position: sticky; top: 0; z-index: 5; background: var(--bg-base); padding: 0.5rem 0; }
.filter-bar label { font-size: 0.82rem; color: var(--text-muted); display: flex; align-items: center; gap: 0.35rem; }
input[type="date"], input[type="search"] { background: var(--bg-input); color: var(--text-base); border: 1px solid var(--border-subtle); border-radius: 4px; padding: 0.3rem 0.5rem; font-size: 0.82rem; font-family: var(--font-mono-font-family); }
input[type="date"]:focus, input[type="search"]:focus { outline: 1px solid var(--link); border-color: var(--link); }
.match-count { font-size: 0.78rem; color: var(--text-muted); margin-left: auto; font-family: var(--font-mono-font-family); }
.btn { padding: 0.3rem 0.75rem; border-radius: 4px; border: 1px solid var(--border-subtle); cursor: pointer; font-size: 0.82rem; font-family: inherit; background: var(--bg-surface-raised); color: var(--text-base); }
.btn:hover { background: var(--bg-surface-hover); }
.timeline { position: relative; }
.spine { position: absolute; left: 120px; top: 0; bottom: 0; width: 2px; background: var(--border-subtle); }
.entries { padding-left: 150px; }
.entry { position: relative; margin-bottom: 1.5rem; }
.entry.hidden { display: none; }
.entry::before { content: ''; position: absolute; left: -30px; top: 0.9rem; width: 28px; height: 2px; background: var(--border-subtle); }
.entry-marker { position: absolute; left: -150px; width: 115px; top: 0.55rem; text-align: right; }
.entry-date { font-size: 0.75rem; font-family: var(--font-mono-font-family); color: var(--link); background: var(--bg-base); border: 1px solid var(--border-subtle); padding: 0.1rem 0.35rem; border-radius: 3px; display: inline-block; }
.entry-card { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--rounded-lg); padding: 1rem 1.25rem; box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 1px 2px rgba(0,0,0,0.4), 0 4px 8px rgba(0,0,0,0.15); }
.entry-title { font-size: 0.95rem; color: var(--text-heading); font-weight: normal; margin-bottom: 0.4rem; }
.entry-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.5rem; }
.tag-pill { font-size: 0.72rem; background: var(--bg-surface-raised); border: 1px solid var(--border-subtle); color: var(--text-muted); border-radius: 10px; padding: 0.1rem 0.5rem; font-family: var(--font-mono-font-family); }
.entry-fields { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.5rem; }
.field { display: grid; grid-template-columns: 160px 1fr; gap: 0.5rem; align-items: start; }
.field-label { font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono-font-family); padding-top: 0.05rem; }
.field-value { font-size: 0.85rem; color: var(--text-base); line-height: 1.45; }
.field-value p { margin: 0; }
.field-value p + p { margin-top: 0.4rem; }
.field-value strong { color: var(--text-heading); font-weight: 600; }
.field-value em { font-style: italic; }
.field-value code { background: var(--bg-code); color: var(--text-code); padding: 0.1em 0.35em; border-radius: 3px; font-family: var(--font-mono-font-family); font-size: 0.88em; }
.field-value a { color: var(--link); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--link) 35%, transparent); transition: color 0.15s ease, border-color 0.15s ease; }
.field-value a:hover { color: var(--link-hover); border-color: var(--link); }
.field-value a:visited { color: var(--link-visited); border-color: color-mix(in srgb, var(--link-visited) 35%, transparent); }
.preamble-body a { color: var(--link); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--link) 35%, transparent); transition: color 0.15s ease, border-color 0.15s ease; }
.preamble-body a:hover { color: var(--link-hover); border-color: var(--link); }
.preamble-body a:visited { color: var(--link-visited); border-color: color-mix(in srgb, var(--link-visited) 35%, transparent); }
.entry-prose { font-size: 0.85rem; color: var(--text-muted); line-height: 1.45; margin-top: 0.4rem; }
.entry-prose p { margin: 0; }
.entry-prose p + p { margin-top: 0.5rem; }
.entry-prose a { color: var(--link); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--link) 35%, transparent); transition: color 0.15s ease, border-color 0.15s ease; }
.entry-prose a:hover { color: var(--link-hover); border-color: var(--link); }
.entry-prose a:visited { color: var(--link-visited); border-color: color-mix(in srgb, var(--link-visited) 35%, transparent); }
footer { margin-top: 2rem; font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono-font-family); }
.code-block-wrapper { position: relative; margin: 0.5rem 0; }
.code-block-wrapper pre { margin: 0; }
.code-copy-btn { position: absolute; top: 0.5rem; right: 0.5rem; background: var(--bg-surface-raised); color: var(--text-muted); border: 1px solid var(--border-subtle); border-radius: var(--rounded-sm); padding: 0.2rem 0.6rem; font-size: 0.75rem; font-family: var(--font-mono-font-family); cursor: pointer; opacity: 0; transition: opacity 0.15s ease, color 0.15s ease; }
.code-block-wrapper:hover .code-copy-btn { opacity: 1; }
.code-copy-btn:hover { color: var(--text-base); border-color: var(--border-emphasis); }
.code-copy-btn.copied { color: var(--severity-ok); border-color: var(--severity-ok); }
@media (max-width: 600px) {
  .spine { display: none; }
  .entries { padding-left: 0; }
  .entry::before { display: none; }
  .entry-marker { position: static; width: auto; text-align: left; margin-bottom: 0.4rem; }
  .field { grid-template-columns: 1fr; gap: 0.15rem; }
}"""

_JS = """\
const allEntries = Array.from(document.querySelectorAll('.entry'));
let newestFirst = true;

function updateCount() {
  const visible = allEntries.filter(e => !e.classList.contains('hidden')).length;
  document.querySelector('.match-count').textContent = visible + ' of ' + allEntries.length + ' entries';
}

function applyFilters() {
  const from = document.getElementById('filter-from').value;
  const to = document.getElementById('filter-to').value;
  const text = document.getElementById('filter-text').value.toLowerCase();
  allEntries.forEach(entry => {
    const date = entry.dataset.date;
    const dateOk = (!from || date >= from) && (!to || date <= to);
    const textOk = !text || entry.textContent.toLowerCase().includes(text);
    entry.classList.toggle('hidden', !(dateOk && textOk));
  });
  updateCount();
}

document.getElementById('filter-from').addEventListener('input', applyFilters);
document.getElementById('filter-to').addEventListener('input', applyFilters);
document.getElementById('filter-text').addEventListener('input', applyFilters);

document.getElementById('sort-toggle').addEventListener('click', () => {
  newestFirst = !newestFirst;
  document.getElementById('sort-toggle').textContent = newestFirst ? 'Newest first' : 'Oldest first';
  const container = document.querySelector('.entries');
  Array.from(container.querySelectorAll('.entry')).reverse().forEach(e => container.appendChild(e));
  updateCount();
});

updateCount();"""


def parse(source_path: Path, options: dict | None = None) -> Timeline:
    """Parse a markdown source file with date-prefixed entries into a Timeline."""
    raw_text = source_path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw_text)

    shape = post.metadata.get("render-html")
    if shape is None:
        raise ValueError(f"{source_path}: missing 'render-html' frontmatter signal")
    if shape != "timeline":
        raise ValueError(f"{source_path}: expected render-html: timeline, got: {shape!r}")

    file_options = post.metadata.get("render-html-options") or {}
    merged = {**file_options, **(options or {})}

    title = str(merged.get("title") or source_path.stem)
    subtitle = str(merged.get("subtitle") or "")
    entry_level = int(merged.get("entry_heading_level", 3))
    tag_field_name: str | None = merged.get("tag_field")

    content = post.content
    matches = [m for m in RE_ENTRY_HEADING.finditer(content) if len(m.group("level")) == entry_level]

    preamble_md = content[: matches[0].start()].strip() if matches else content.strip()

    entries: list[Entry] = []
    for i, m in enumerate(matches):
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[body_start:body_end]

        fields: list[Field] = []
        field_spans: list[tuple[int, int]] = []
        for fm in RE_FIELD.finditer(body):
            fields.append(Field(name=fm.group("field").strip(), value_md=fm.group("value").strip()))
            field_spans.append((fm.start(), fm.end()))

        prose_parts: list[str] = []
        pos = 0
        for start, end in field_spans:
            chunk = body[pos:start].strip()
            if chunk:
                prose_parts.append(chunk)
            pos = end
        chunk = body[pos:].strip()
        if chunk:
            prose_parts.append(chunk)
        prose_md = "\n\n".join(prose_parts)

        tags: list[str] = []
        if tag_field_name:
            for f in fields:
                if f.name.lower() == tag_field_name.lower():
                    tags = [t.strip() for t in _TAG_SPLIT.split(f.value_md) if t.strip()]
                    break

        entries.append(Entry(
            date=m.group("date"),
            title=m.group("title").strip(),
            fields=fields,
            prose_md=prose_md,
            tags=tags,
        ))

    return Timeline(
        title=title,
        subtitle=subtitle,
        source_path=source_path,
        preamble_md=preamble_md,
        entries=entries,
    )


def render(source_path: Path, options: dict | None = None) -> str:
    """Render a Timeline as a self-contained HTML string."""
    timeline = parse(source_path, options)
    return _render_html(timeline)


def _render_html(timeline: Timeline) -> str:
    render_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title_esc = html.escape(timeline.title)
    source_esc = html.escape(str(timeline.source_path))
    n = len(timeline.entries)

    subtitle_html = f'      <div class="subtitle">{html.escape(timeline.subtitle)}</div>\n' if timeline.subtitle else ""

    preamble_html = ""
    if timeline.preamble_md:
        preamble_body = render_inline_markdown(timeline.preamble_md)
        preamble_html = (
            '\n    <details class="preamble" open>\n'
            '      <summary>Preamble &amp; Format</summary>\n'
            f'      <div class="preamble-body">{preamble_body}</div>\n'
            "    </details>"
        )

    sorted_entries = sorted(timeline.entries, key=lambda e: e.date, reverse=True)
    entries_html = "\n".join(_render_entry(e) for e in sorted_entries)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_esc}</title>
  <style>{get_theme_css()}
{_CSS}</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>{title_esc}</h1>
{subtitle_html}      <div class="meta">{source_esc} &middot; rendered {render_date} &middot; {n} entries</div>
    </header>{preamble_html}
    <div class="filter-bar">
      <label>From <input type="date" id="filter-from"></label>
      <label>To <input type="date" id="filter-to"></label>
      <input type="search" id="filter-text" placeholder="Filter entries...">
      <button id="sort-toggle" class="btn">Newest first</button>
      <span class="match-count">{n} entries</span>
    </div>
    <div class="timeline">
      <div class="spine"></div>
      <div class="entries">
{entries_html}
      </div>
    </div>
    <footer>generated by cowork-render timeline v1 &middot; {render_date}</footer>
  </div>
  <script>{get_copy_button_js()}
{_JS}</script>
</body>
</html>"""


def _render_entry(entry: Entry) -> str:
    date_esc = html.escape(entry.date)
    title_esc = html.escape(entry.title)

    tags_html = ""
    if entry.tags:
        pills = "".join(f'<span class="tag-pill">{html.escape(t)}</span>' for t in entry.tags)
        tags_html = f'\n          <div class="entry-tags">{pills}</div>'

    fields_html = ""
    if entry.fields:
        rows = "".join(_render_field(f) for f in entry.fields)
        fields_html = f'\n          <div class="entry-fields">{rows}\n          </div>'

    prose_html = ""
    if entry.prose_md:
        prose_html = f'\n          <div class="entry-prose">{render_inline_markdown(entry.prose_md)}</div>'

    return (
        f'        <article class="entry" data-date="{date_esc}">\n'
        f'          <div class="entry-marker">'
        f'<time class="entry-date" datetime="{date_esc}">{date_esc}</time></div>\n'
        f'          <div class="entry-card">\n'
        f'            <h3 class="entry-title">{title_esc}</h3>'
        f"{tags_html}{fields_html}{prose_html}\n"
        f"          </div>\n"
        f"        </article>"
    )


def _render_field(f: Field) -> str:
    name_esc = html.escape(f.name)
    value_html = render_inline_markdown(f.value_md) if f.value_md else ""
    return (
        f'\n            <div class="field">'
        f'<span class="field-label">{name_esc}</span>'
        f'<div class="field-value">{value_html}</div>'
        f"</div>"
    )
