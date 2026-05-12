"""Dashboard renderer — produces sortable filterable HTML from markdown tables."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

from cowork_render._markdown import get_copy_button_js, render_block, render_inline
from cowork_render.theme import get_diagram_css, get_theme_css


_BOOLEAN_RE = re.compile(r'^[✓✗✔✘]$|^(?:yes|no|true|false)$', re.IGNORECASE)
_DATE_RE = re.compile(r'^\d{4}[-/]\d{2}[-/]\d{2}$')
_NUMBER_RE = re.compile(r'^\$?\d[\d,]*(?:\.\d+)?%?$')
_STATUS_KEYWORDS = {
    'active', 'done', 'blocked', 'parked', 'queued', 'deferred',
    'ok', 'warning', 'error', 'broken', 'pending', 'shipped',
}
_STATUS_GREEN = {'active', 'ok', 'done', 'shipped'}
_STATUS_GRAY = {'pending', 'queued', 'parked', 'deferred'}
_STATUS_RED = {'blocked', 'error', 'broken'}
_STATUS_ORANGE = {'warning'}


@dataclass
class Column:
    name: str
    detected_type: str  # 'text' | 'number' | 'date' | 'boolean' | 'status'
    is_key: bool = False


@dataclass
class SubsectionBlock:
    heading: str
    notes_md: str
    columns: list[Column]
    rows: list[list[str]]


@dataclass
class TableBlock:
    heading: str
    notes_md: str
    columns: list[Column]
    rows: list[list[str]]
    subsections: list[SubsectionBlock] = field(default_factory=list)


@dataclass
class ProseBlock:
    heading: str
    body_md: str



@dataclass
class Dashboard:
    title: str
    subtitle: str
    source_path: Path
    tables: list[TableBlock]           # table blocks only, for test access
    blocks: list                       # ordered: TableBlock | ProseBlock
    preamble_md: str


_CSS = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg-base); color: var(--text-base); font-family: Georgia, 'Times New Roman', serif; font-size: var(--font-body-font-size); line-height: var(--font-body-line-height); min-height: 100vh; }
.container { max-width: 1500px; margin: 0 auto; padding: 1.5rem; }
header { margin-bottom: 1.75rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-subtle); position: relative; }
header::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 80px; height: 2px; background: linear-gradient(90deg, var(--link), var(--severity-ok)); border-radius: 999px; }
header h1 { font-size: 1.6rem; color: var(--text-heading); margin-bottom: 0.25rem; }
.subtitle { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.4rem; }
.meta { font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono-font-family); }
.preamble { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--rounded-lg); padding: 0.75rem 1rem; margin-bottom: 1.25rem; font-size: 0.85rem; color: var(--text-muted); line-height: 1.55; box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 1px 2px rgba(0,0,0,0.4), 0 4px 8px rgba(0,0,0,0.15); }
.preamble p { margin: 0; }
.preamble p + p { margin-top: 0.5rem; }
.preamble ul, .preamble ol { padding-left: 1.5rem; margin: 0.35rem 0; }
.preamble li { margin-bottom: 0.2rem; line-height: 1.5; }
.preamble code { background: var(--bg-code); color: var(--text-code); padding: 0.15em 0.4em; border-radius: 3px; font-size: 0.88em; font-family: var(--font-mono-font-family); }
.preamble pre { background: var(--bg-code); border: 1px solid var(--border-subtle); border-radius: var(--rounded-md); padding: 0.6rem 0.9rem; margin: 0.5rem 0; max-width: 100%; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
.preamble pre code { background: none; padding: 0; border-radius: 0; font-family: var(--font-mono-font-family); font-size: 0.88em; line-height: 1.55; color: var(--text-base); white-space: pre-wrap; word-wrap: break-word; }
.preamble blockquote { border-left: 3px solid var(--border-subtle); padding-left: 0.75rem; margin: 0.25rem 0; color: var(--text-muted); }
.preamble a { color: var(--link); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--link) 35%, transparent); transition: color 0.15s ease, border-color 0.15s ease; }
.preamble a:hover { color: var(--link-hover); border-color: var(--link); }
.preamble a:visited { color: var(--link-visited); border-color: color-mix(in srgb, var(--link-visited) 35%, transparent); }
.filter-bar { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; position: sticky; top: 0; z-index: 5; background: var(--bg-base); padding: 0.5rem 0; }
input[type="search"] { background: var(--bg-input); color: var(--text-base); border: 1px solid var(--border-subtle); border-radius: 4px; padding: 0.35rem 0.6rem; font-size: 0.82rem; font-family: var(--font-mono-font-family); width: 240px; }
input[type="search"]:focus { outline: 1px solid var(--link); border-color: var(--link); }
.match-count { font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono-font-family); }
.table-section { margin-bottom: 2rem; box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 1px 2px rgba(0,0,0,0.4), 0 4px 8px rgba(0,0,0,0.15); border-radius: var(--rounded-lg); }
.section-heading { font-size: 0.95rem; font-weight: 600; color: var(--text-strong); margin-bottom: 0.75rem; padding-bottom: 0.3rem; border-bottom: 1px solid var(--border-subtle); font-family: var(--font-mono-font-family); }
.section-notes { font-size: 0.83rem; color: var(--text-muted); margin-bottom: 0.65rem; line-height: 1.5; }
.section-notes p { margin: 0; }
.section-notes p + p { margin-top: 0.4rem; }
.section-notes a { color: var(--link); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--link) 35%, transparent); transition: color 0.15s ease, border-color 0.15s ease; }
.section-notes a:hover { color: var(--link-hover); border-color: var(--link); }
.section-notes a:visited { color: var(--link-visited); border-color: color-mix(in srgb, var(--link-visited) 35%, transparent); }
.section-notes code { background: var(--bg-code); color: var(--text-code); padding: 0.15em 0.4em; border-radius: 3px; font-size: 0.88em; font-family: var(--font-mono-font-family); }
.section-notes ul, .section-notes ol { padding-left: 1.5rem; margin: 0.35rem 0; }
.section-notes li { margin-bottom: 0.2rem; line-height: 1.5; }
.section-notes pre { background: var(--bg-code); border: 1px solid var(--border-subtle); border-radius: var(--rounded-md); padding: 0.6rem 0.9rem; margin: 0.5rem 0; max-width: 100%; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
.section-notes pre code { background: none; padding: 0; border-radius: 0; font-family: var(--font-mono-font-family); font-size: 0.88em; line-height: 1.55; color: var(--text-base); white-space: pre-wrap; word-wrap: break-word; }
.subsection-notes pre { background: var(--bg-code); border: 1px solid var(--border-subtle); border-radius: var(--rounded-md); padding: 0.6rem 0.9rem; margin: 0.5rem 0; max-width: 100%; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
.subsection-notes pre code { background: none; padding: 0; border-radius: 0; font-family: var(--font-mono-font-family); font-size: 0.88em; line-height: 1.55; color: var(--text-base); white-space: pre-wrap; word-wrap: break-word; }
.subsection { margin-top: 1rem; padding-left: 0.75rem; border-left: 2px solid var(--border-subtle); }
.subsection-heading { font-size: 0.88rem; font-weight: 600; color: var(--text-strong); margin-bottom: 0.4rem; padding-bottom: 0.25rem; font-family: var(--font-mono-font-family); }
.subsection-notes { font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.55rem; line-height: 1.5; }
.table-wrap { overflow-x: auto; border: 1px solid var(--border-subtle); border-radius: var(--rounded-lg); }
table.dashboard { border-collapse: collapse; width: 100%; }
thead { position: sticky; top: 0; z-index: 1; }
thead tr { background: var(--bg-surface); }
th { padding: 0.55rem 0.75rem; text-align: left; color: var(--text-heading); font-weight: 600; font-size: 0.8rem; border-bottom: 2px solid var(--border-subtle); white-space: nowrap; }
th.sortable { cursor: pointer; user-select: none; }
th.sortable:hover { background: var(--bg-surface-raised); }
.sort-chevron { font-size: 0.7rem; color: var(--link); }
tbody tr { border-bottom: 1px solid var(--border-subtle); }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: var(--bg-surface); }
td { padding: 0.45rem 0.75rem; font-size: 0.85rem; vertical-align: middle; }
td code { background: var(--bg-code); color: var(--text-code); padding: 0.1em 0.35em; border-radius: 3px; font-size: 0.82em; font-family: var(--font-mono-font-family); word-break: break-all; }
td a { color: var(--link); text-decoration: none; }
td a:hover { text-decoration: underline; }
.pill { display: inline-block; padding: 0.1em 0.5em; border-radius: 10px; font-size: 0.8em; font-weight: 600; line-height: 1.4; }
.cell-bool-yes { text-align: center; }
.cell-bool-yes .pill { background: var(--severity-ok); color: #fff; }
.cell-bool-no { text-align: center; }
.cell-bool-no .pill { background: var(--severity-high); color: #fff; }
.cell-date-fresh { color: var(--severity-ok); font-family: var(--font-mono-font-family); font-size: 0.82em; }
.cell-date-recent { color: var(--severity-low); font-family: var(--font-mono-font-family); font-size: 0.82em; }
.cell-date-aging { color: var(--severity-medium); font-family: var(--font-mono-font-family); font-size: 0.82em; }
.cell-date-stale { color: var(--severity-high); font-family: var(--font-mono-font-family); font-size: 0.82em; }
.cell-status-green .pill { background: var(--severity-ok); color: #fff; }
.cell-status-gray .pill { background: #6e7681; color: #fff; }
.cell-status-red .pill { background: var(--severity-high); color: #fff; }
.cell-status-orange .pill { background: var(--severity-low); color: #fff; }
.cell-number { font-family: var(--font-mono-font-family); font-size: 0.82em; text-align: right; }
.commentary-section { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--rounded-lg); padding: 0.75rem 1rem; margin-bottom: 0.75rem; box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 1px 2px rgba(0,0,0,0.4), 0 4px 8px rgba(0,0,0,0.15); }
.commentary-section summary { color: var(--text-heading); cursor: pointer; font-size: 0.9rem; user-select: none; }
.commentary-body { margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-muted); line-height: 1.55; }
.commentary-body p { margin: 0; }
.commentary-body p + p { margin-top: 0.5rem; }
.commentary-body a { color: var(--link); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--link) 35%, transparent); transition: color 0.15s ease, border-color 0.15s ease; }
.commentary-body a:hover { color: var(--link-hover); border-color: var(--link); }
.commentary-body a:visited { color: var(--link-visited); border-color: color-mix(in srgb, var(--link-visited) 35%, transparent); }
.commentary-body code { background: var(--bg-code); color: var(--text-code); padding: 0.15em 0.4em; border-radius: 3px; font-size: 0.88em; font-family: var(--font-mono-font-family); }
.commentary-body ul, .commentary-body ol { padding-left: 1.5rem; margin: 0.4rem 0; }
.commentary-body li { margin-bottom: 0.25rem; font-size: 0.85rem; line-height: 1.5; }
.commentary-body pre { background: var(--bg-code); border: 1px solid var(--border-subtle); border-radius: var(--rounded-md); padding: 0.6rem 0.9rem; margin: 0.5rem 0; max-width: 100%; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
.commentary-body pre code { background: none; padding: 0; border-radius: 0; font-family: var(--font-mono-font-family); font-size: 0.88em; line-height: 1.55; color: var(--text-base); white-space: pre-wrap; word-wrap: break-word; }
footer { margin-top: 1.5rem; font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono-font-family); }
@media (max-width: 600px) { .table-wrap { border: none; border-radius: 0; } }
.code-block-wrapper { position: relative; margin: 0.5rem 0; }
.code-block-wrapper pre { margin: 0; white-space: pre; word-wrap: normal; }
.code-copy-btn { position: absolute; top: 0.5rem; right: 0.5rem; background: var(--bg-surface-raised); color: var(--text-muted); border: 1px solid var(--border-subtle); border-radius: var(--rounded-sm); padding: 0.2rem 0.6rem; font-size: 0.75rem; font-family: var(--font-mono-font-family); cursor: pointer; opacity: 0; transition: opacity 0.15s ease, color 0.15s ease; }
.code-block-wrapper:hover .code-copy-btn { opacity: 1; }
.code-copy-btn:hover { color: var(--text-base); border-color: var(--border-emphasis); }
.code-copy-btn.copied { color: var(--severity-ok); border-color: var(--severity-ok); }"""

_JS = """\
const STATUS_ORDER = {active:0,ok:0,done:0,shipped:0,pending:1,queued:1,parked:1,deferred:1,warning:2,blocked:3,error:3,broken:3};

function boolVal(v) {
  if (/^[✓✔]$|^yes$|^true$/i.test(v)) return 1;
  if (/^[✗✘]$|^no$|^false$/i.test(v)) return 0;
  return -1;
}

function compareRows(a, b, col, type, dir) {
  const av = a.querySelectorAll('td')[col]?.textContent.trim() ?? '';
  const bv = b.querySelectorAll('td')[col]?.textContent.trim() ?? '';
  let cmp = 0;
  if (type === 'number') cmp = parseFloat(av.replace(/[$,%]/g,'') || '0') - parseFloat(bv.replace(/[$,%]/g,'') || '0');
  else if (type === 'date') cmp = av.localeCompare(bv);
  else if (type === 'boolean') cmp = boolVal(av) - boolVal(bv);
  else if (type === 'status') cmp = (STATUS_ORDER[av.toLowerCase()] ?? 99) - (STATUS_ORDER[bv.toLowerCase()] ?? 99);
  else cmp = av.localeCompare(bv);
  return cmp * dir;
}

document.querySelectorAll('table.dashboard').forEach(table => {
  const tbody = table.querySelector('tbody');
  let sortCol = -1, sortDir = 0;

  table.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const col = parseInt(th.dataset.col);
      const type = th.dataset.type;
      if (sortCol === col) {
        sortDir = sortDir === 1 ? -1 : sortDir === -1 ? 0 : 1;
      } else {
        sortCol = col; sortDir = 1;
      }
      table.querySelectorAll('.sort-chevron').forEach(c => c.textContent = '');
      const chevron = th.querySelector('.sort-chevron');
      if (chevron) chevron.textContent = sortDir === 1 ? ' ▲' : sortDir === -1 ? ' ▼' : '';
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const sorted = sortDir === 0 ? rows : [...rows].sort((a, b) => compareRows(a, b, col, type, sortDir));
      sorted.forEach(r => tbody.appendChild(r));
      applyFilter();
    });
  });
});

const filterInput = document.getElementById('filter');
function applyFilter() {
  const q = filterInput.value.toLowerCase();
  let total = 0, visible = 0;
  document.querySelectorAll('table.dashboard tbody tr').forEach(row => {
    const match = !q || row.textContent.toLowerCase().includes(q);
    row.style.display = match ? '' : 'none';
    total++;
    if (match) visible++;
  });
  document.querySelector('.match-count').textContent = visible + ' of ' + total + ' rows';
}
filterInput.addEventListener('input', applyFilter);
applyFilter();"""


def _detect_column_type(values: list[str]) -> str:
    non_empty = [v.strip() for v in values if v.strip()]
    if not non_empty:
        return 'text'
    threshold = len(non_empty) * 0.8
    if sum(1 for v in non_empty if _BOOLEAN_RE.match(v)) >= threshold:
        return 'boolean'
    if sum(1 for v in non_empty if _DATE_RE.match(v)) >= threshold:
        return 'date'
    if sum(1 for v in non_empty if _NUMBER_RE.match(v)) >= threshold:
        return 'number'
    if sum(1 for v in non_empty if v.lower() in _STATUS_KEYWORDS) >= threshold:
        return 'status'
    return 'text'


def _cell_class(value: str, col_type: str) -> str:
    v = value.strip()
    vl = v.lower()
    if col_type == 'boolean':
        if v in {'✓', '✔'} or vl in {'yes', 'true'}:
            return 'cell-bool-yes'
        if v in {'✗', '✘'} or vl in {'no', 'false'}:
            return 'cell-bool-no'
    elif col_type == 'date':
        if _DATE_RE.match(v):
            try:
                d = datetime.strptime(v[:10].replace('/', '-'), '%Y-%m-%d').date()
                days = (datetime.now(timezone.utc).date() - d).days
                if days <= 30:
                    return 'cell-date-fresh'
                if days <= 90:
                    return 'cell-date-recent'
                if days <= 180:
                    return 'cell-date-aging'
                return 'cell-date-stale'
            except ValueError:
                pass
    elif col_type == 'status':
        if vl in _STATUS_GREEN:
            return 'cell-status-green'
        if vl in _STATUS_GRAY:
            return 'cell-status-gray'
        if vl in _STATUS_RED:
            return 'cell-status-red'
        if vl in _STATUS_ORANGE:
            return 'cell-status-orange'
    elif col_type == 'number':
        return 'cell-number'
    return 'cell-text'




def _table_from_lines_standalone(seg: list[str]) -> tuple[str, list[str]]:
    """Return (notes_md, table_lines) from a block of lines, or (body_md, []) if no table."""
    tstart = next((j for j, ln in enumerate(seg) if ln.strip().startswith('|')), None)
    if tstart is None:
        return '\n'.join(seg).strip(), []
    notes = '\n'.join(seg[:tstart]).strip()
    tend = tstart
    while tend < len(seg) and seg[tend].strip().startswith('|'):
        tend += 1
    return notes, seg[tstart:tend]


def _extract_all_tables(content: str):
    """Extract all markdown tables and prose-only sections in document order.

    Returns (ordered_items, preamble). ordered_items entries:
      ('table', heading, notes_md, table_lines)         — section with a table
      ('prose', heading, body_md)                       — section with prose only
      ('section_with_subs', heading, notes_md, subs)    — H3 section containing H4 subsections,
                                                          subs is list of (h4_heading, sub_lines)
    Preamble is content before the first H2.
    H4 headings are not top-level sections — they become subsections of their parent H3.
    """
    lines = content.splitlines()

    first_h2_idx = next((i for i, ln in enumerate(lines) if re.match(r'^## ', ln)), None)
    if first_h2_idx is not None:
        preamble = '\n'.join(lines[:first_h2_idx]).strip()
        body = lines[first_h2_idx:]
    else:
        preamble = ''
        body = lines

    _H4_RE = re.compile(r'^#### (.+)')

    def _flush_section(heading: str, section_lines: list[str], out: list) -> None:
        if not heading and not any(ln.strip().startswith('|') for ln in section_lines):
            return
        h4_idxs = [j for j, ln in enumerate(section_lines) if _H4_RE.match(ln)]
        if h4_idxs:
            notes_md = '\n'.join(section_lines[:h4_idxs[0]]).strip()
            subs = []
            for k, h4_idx in enumerate(h4_idxs):
                h4_heading = _H4_RE.match(section_lines[h4_idx]).group(1).strip()
                sub_end = h4_idxs[k + 1] if k + 1 < len(h4_idxs) else len(section_lines)
                subs.append((h4_heading, section_lines[h4_idx + 1:sub_end]))
            out.append(('section_with_subs', heading, notes_md, subs))
        else:
            notes_md, table_lines = _table_from_lines_standalone(section_lines)
            if table_lines:
                out.append(('table', heading, notes_md, table_lines))
            elif notes_md:
                out.append(('prose', heading, notes_md))

    ordered_items: list[tuple] = []
    last_heading = ''
    last_content_start = 0
    _SEC_RE = re.compile(r'^(#{2,3}) (.+)')

    i = 0
    while i < len(body):
        hm = _SEC_RE.match(body[i])
        if hm:
            _flush_section(last_heading, body[last_content_start:i], ordered_items)
            last_heading = hm.group(2).strip()
            last_content_start = i + 1
        i += 1

    _flush_section(last_heading, body[last_content_start:], ordered_items)
    return ordered_items, preamble


def _parse_table_rows(table_lines: list[str]):
    def split_row(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip('|').split('|')]

    def is_separator(cells: list[str]) -> bool:
        return bool(cells) and all(re.match(r'^[-: ]+$', c) for c in cells if c)

    all_rows = [split_row(ln) for ln in table_lines if ln.strip()]
    if not all_rows:
        return [], []
    headers = all_rows[0]
    data_rows, found_sep = [], False
    for row in all_rows[1:]:
        if not found_sep and is_separator(row):
            found_sep = True
            continue
        data_rows.append(row)
    return headers, data_rows



def parse(source_path: Path) -> Dashboard:
    raw_text = source_path.read_text(encoding='utf-8')
    post = frontmatter.loads(raw_text)

    shape = post.metadata.get('render-html')
    if shape is None:
        raise ValueError(f'{source_path}: missing \'render-html\' frontmatter signal')
    if shape != 'dashboard':
        raise ValueError(f'{source_path}: expected render-html: dashboard, got: {shape!r}')

    options = post.metadata.get('render-html-options') or {}
    title = str(options.get('title') or source_path.stem)
    subtitle = str(options.get('subtitle') or '')
    key_column: str | None = options.get('key_column')
    column_types_override: dict[str, str] = dict(options.get('column_types') or {})

    ordered_items, preamble_text = _extract_all_tables(post.content)
    if not any(it[0] in ('table', 'section_with_subs') for it in ordered_items):
        raise ValueError(f'{source_path}: dashboard requires a primary markdown table')

    def _build_columns(headers: list[str], data_rows: list[list[str]]) -> list[Column]:
        cols = []
        for i, name in enumerate(headers):
            if name in column_types_override:
                col_type = str(column_types_override[name])
            else:
                col_values = [row[i] if i < len(row) else '' for row in data_rows]
                col_type = _detect_column_type(col_values)
            is_key = (name == key_column) if key_column else (i == 0)
            cols.append(Column(name=name, detected_type=col_type, is_key=is_key))
        return cols

    blocks: list = []
    table_blocks: list[TableBlock] = []
    for item in ordered_items:
        if item[0] == 'prose':
            _, heading, body_md = item
            blocks.append(ProseBlock(heading=heading, body_md=body_md))
        elif item[0] == 'section_with_subs':
            _, heading, notes_md, subs = item
            subsections = []
            for h4_heading, sub_lines in subs:
                sub_notes, sub_table_lines = _table_from_lines_standalone(sub_lines)
                sub_headers, sub_rows = _parse_table_rows(sub_table_lines)
                if not sub_headers:
                    if sub_notes:
                        subsections.append(SubsectionBlock(
                            heading=h4_heading, notes_md=sub_notes,
                            columns=[], rows=[],
                        ))
                    continue
                sub_cols = _build_columns(sub_headers, sub_rows)
                subsections.append(SubsectionBlock(
                    heading=h4_heading, notes_md=sub_notes,
                    columns=sub_cols, rows=sub_rows,
                ))
            tb = TableBlock(heading=heading, notes_md=notes_md,
                            columns=[], rows=[], subsections=subsections)
            blocks.append(tb)
            table_blocks.append(tb)
        else:
            _, heading, notes_md, table_lines = item
            headers, data_rows = _parse_table_rows(table_lines)
            if not headers:
                continue
            columns = _build_columns(headers, data_rows)
            tb = TableBlock(heading=heading, notes_md=notes_md, columns=columns, rows=data_rows)
            blocks.append(tb)
            table_blocks.append(tb)

    if not table_blocks:
        raise ValueError(f'{source_path}: dashboard requires a primary markdown table')

    return Dashboard(
        title=title,
        subtitle=subtitle,
        source_path=source_path,
        tables=table_blocks,
        blocks=blocks,
        preamble_md=preamble_text,
    )


def render(source_path: Path, options: dict | None = None) -> str:
    return _render_html(parse(source_path))


def _render_html(db: Dashboard) -> str:
    render_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    title_esc = html.escape(db.title)
    source_esc = html.escape(str(db.source_path))
    total_rows = sum(len(t.rows) for t in db.tables)
    n_tables = len(db.tables)

    subtitle_html = (
        f'      <div class="subtitle">{html.escape(db.subtitle)}</div>\n'
        if db.subtitle else ''
    )
    preamble_html = (
        f'\n    <section class="preamble">{render_block(db.preamble_md)}</section>'
        if db.preamble_md else ''
    )
    meta_detail = f'{n_tables} tables &middot; {total_rows} rows' if n_tables > 1 else f'{total_rows} rows'
    table_idx = 0
    block_parts = []
    for block in db.blocks:
        if isinstance(block, TableBlock):
            block_parts.append(_render_table_section(block, table_idx))
            table_idx += max(1, len(block.subsections))
        else:
            block_parts.append(_render_prose_section(block))
    tables_html = '\n'.join(block_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_esc}</title>
  <style>{get_theme_css()}
{get_diagram_css()}
{_CSS}</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>{title_esc}</h1>
{subtitle_html}      <div class="meta">{source_esc} &middot; rendered {render_date} &middot; {meta_detail}</div>
    </header>{preamble_html}
    <div class="filter-bar">
      <input type="search" id="filter" placeholder="Filter rows...">
      <span class="match-count">{total_rows} rows</span>
    </div>
{tables_html}
    <footer>generated by cowork-render dashboard v1 &middot; {render_date}</footer>
  </div>
  <script>{get_copy_button_js()}
{_JS}</script>
</body>
</html>"""


def _render_subsection(sub: SubsectionBlock, idx: int) -> str:
    heading_html = (
        f'      <h3 class="subsection-heading">{render_inline(sub.heading)}</h3>\n'
        if sub.heading else ''
    )
    notes_html = (
        f'      <div class="subsection-notes">{render_block(sub.notes_md)}</div>\n'
        if sub.notes_md else ''
    )
    if not sub.columns:
        return (
            f'      <div class="subsection">\n'
            f'{heading_html}'
            f'{notes_html}'
            f'      </div>'
        )
    thead = _render_thead(sub.columns)
    tbody_html = _render_tbody(sub.columns, sub.rows)
    return (
        f'      <div class="subsection">\n'
        f'{heading_html}'
        f'{notes_html}'
        f'        <div class="table-wrap">\n'
        f'          <table class="dashboard" data-table-index="{idx}">\n'
        f'            <thead>\n{thead}\n            </thead>\n'
        f'            <tbody>\n{tbody_html}\n            </tbody>\n'
        f'          </table>\n'
        f'        </div>\n'
        f'      </div>'
    )


def _render_table_section(table: TableBlock, idx: int) -> str:
    heading_html = (
        f'      <h2 class="section-heading">{render_inline(table.heading)}</h2>\n'
        if table.heading else ''
    )
    notes_html = (
        f'      <div class="section-notes">{render_block(table.notes_md)}</div>\n'
        if table.notes_md else ''
    )

    if table.subsections:
        sub_parts = []
        for sub in table.subsections:
            sub_parts.append(_render_subsection(sub, idx))
            idx += 1
        return (
            f'    <section class="table-section">\n'
            f'{heading_html}'
            f'{notes_html}'
            + '\n'.join(sub_parts) + '\n'
            + '    </section>'
        )

    thead = _render_thead(table.columns)
    tbody_html = _render_tbody(table.columns, table.rows)
    return (
        f'    <section class="table-section">\n'
        f'{heading_html}'
        f'{notes_html}'
        f'      <div class="table-wrap">\n'
        f'        <table class="dashboard" data-table-index="{idx}">\n'
        f'          <thead>\n{thead}\n          </thead>\n'
        f'          <tbody>\n{tbody_html}\n          </tbody>\n'
        f'        </table>\n'
        f'      </div>\n'
        f'    </section>'
    )


def _render_prose_section(block: ProseBlock) -> str:
    heading_html = (
        f'      <h2 class="section-heading">{render_inline(block.heading)}</h2>\n'
        if block.heading else ''
    )
    body_html = render_block(block.body_md)
    return (
        f'    <section class="table-section">\n'
        f'{heading_html}'
        f'      <div class="section-notes">{body_html}</div>\n'
        f'    </section>'
    )


def _render_thead(columns: list[Column]) -> str:
    cells = ''.join(
        f'            <th data-col="{i}" data-type="{col.detected_type}" class="sortable">'
        f'{html.escape(col.name)} <span class="sort-chevron"></span></th>\n'
        for i, col in enumerate(columns)
    )
    return f'          <tr>\n{cells}          </tr>'


def _render_tbody(columns: list[Column], rows: list[list[str]]) -> str:
    if not rows:
        n = len(columns)
        return f'          <tr><td colspan="{n}" style="text-align:center;color:#8b949e;padding:1rem;">No data</td></tr>'
    return '\n'.join(_render_row(columns, row) for row in rows)


def _render_row(columns: list[Column], row: list[str]) -> str:
    cells = ''.join(_render_cell(col, row[i] if i < len(row) else '') for i, col in enumerate(columns))
    return f'          <tr>\n{cells}          </tr>'


def _render_cell(col: Column, value: str) -> str:
    cls = _cell_class(value, col.detected_type)
    name_esc = html.escape(col.name)
    value_esc = html.escape(value)
    if cls.startswith('cell-bool-') or cls.startswith('cell-status-'):
        content = f'<span class="pill">{value_esc}</span>'
    else:
        content = render_inline(value)
    return f'            <td class="{cls}" data-cell="{name_esc}">{content}</td>\n'


