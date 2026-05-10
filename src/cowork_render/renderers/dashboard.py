"""Dashboard renderer — produces sortable filterable HTML table from a markdown table."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

from cowork_render.renderers._inline import render_inline_markdown


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
class Section:
    heading: str
    body_md: str


@dataclass
class Dashboard:
    title: str
    subtitle: str
    source_path: Path
    columns: list[Column]
    rows: list[list[str]]
    preamble_md: str
    post_table_sections: list[Section]


_CSS = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #16161a; color: #e1e4e8; font-family: Georgia, 'Times New Roman', serif; min-height: 100vh; }
.container { max-width: 1400px; margin: 0 auto; padding: 1.5rem; }
header { margin-bottom: 1.5rem; }
header h1 { font-size: 1.6rem; color: #f0f3f6; margin-bottom: 0.25rem; }
.subtitle { font-size: 0.9rem; color: #8b949e; margin-bottom: 0.4rem; }
.meta { font-size: 0.78rem; color: #8b949e; font-family: 'SF Mono', Menlo, Consolas, monospace; }
.preamble { background: #1f2128; border: 1px solid #2d3138; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1.25rem; font-size: 0.85rem; color: #8b949e; line-height: 1.55; }
.preamble p { margin: 0; }
.preamble p + p { margin-top: 0.5rem; }
.filter-bar { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
input[type="search"] { background: #1f2128; color: #e1e4e8; border: 1px solid #2d3138; border-radius: 4px; padding: 0.35rem 0.6rem; font-size: 0.82rem; font-family: 'SF Mono', Menlo, Consolas, monospace; width: 240px; }
input[type="search"]:focus { outline: 1px solid #58a6ff; border-color: #58a6ff; }
.match-count { font-size: 0.78rem; color: #8b949e; font-family: 'SF Mono', Menlo, Consolas, monospace; }
.table-wrap { overflow-x: auto; border: 1px solid #2d3138; border-radius: 6px; margin-bottom: 1.25rem; }
table.dashboard { border-collapse: collapse; width: 100%; }
thead { position: sticky; top: 0; z-index: 1; }
thead tr { background: #1f2128; }
th { padding: 0.55rem 0.75rem; text-align: left; color: #f0f3f6; font-weight: 600; font-size: 0.8rem; border-bottom: 2px solid #2d3138; white-space: nowrap; }
th.sortable { cursor: pointer; user-select: none; }
th.sortable:hover { background: #25272e; }
.sort-chevron { font-size: 0.7rem; color: #58a6ff; }
tbody tr { border-bottom: 1px solid #2d3138; }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: #1f2128; }
td { padding: 0.45rem 0.75rem; font-size: 0.85rem; vertical-align: middle; }
/* pill helper — shared by boolean and status cells */
.pill { display: inline-block; padding: 0.1em 0.5em; border-radius: 10px; font-size: 0.8em; font-weight: 600; line-height: 1.4; }
/* boolean */
.cell-bool-yes { text-align: center; }
.cell-bool-yes .pill { background: #3fb950; color: #fff; }
.cell-bool-no { text-align: center; }
.cell-bool-no .pill { background: #f85149; color: #fff; }
/* date — color by freshness, mono font */
.cell-date-fresh { color: #3fb950; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.82em; }
.cell-date-recent { color: #d29922; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.82em; }
.cell-date-aging { color: #e3b341; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.82em; }
.cell-date-stale { color: #f85149; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.82em; }
/* status */
.cell-status-green .pill { background: #3fb950; color: #fff; }
.cell-status-gray .pill { background: #6e7681; color: #fff; }
.cell-status-red .pill { background: #f85149; color: #fff; }
.cell-status-orange .pill { background: #d29922; color: #fff; }
/* number */
.cell-number { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.82em; text-align: right; }
/* commentary panels */
.commentary-section { background: #1f2128; border: 1px solid #2d3138; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.75rem; }
.commentary-section summary { color: #f0f3f6; cursor: pointer; font-size: 0.9rem; user-select: none; }
.commentary-body { margin-top: 0.75rem; font-size: 0.85rem; color: #8b949e; line-height: 1.55; }
.commentary-body p { margin: 0; }
.commentary-body p + p { margin-top: 0.5rem; }
footer { margin-top: 1.5rem; font-size: 0.75rem; color: #8b949e; font-family: 'SF Mono', Menlo, Consolas, monospace; }
@media (max-width: 600px) { .table-wrap { border: none; border-radius: 0; } }"""

_JS = """\
const tbody = document.querySelector('.dashboard tbody');
const allRows = Array.from(tbody.querySelectorAll('tr'));
let sortCol = -1, sortDir = 0;

const STATUS_ORDER = {active:0,ok:0,done:0,shipped:0,pending:1,queued:1,parked:1,deferred:1,warning:2,blocked:3,error:3,broken:3};

function boolVal(v) {
  if (/^[\\u2713\\u2714]$|^yes$|^true$/i.test(v)) return 1;
  if (/^[\\u2717\\u2718]$|^no$|^false$/i.test(v)) return 0;
  return -1;
}

function cellText(row, col) {
  const td = row.querySelectorAll('td')[col];
  return td ? td.textContent.trim() : '';
}

function compareRows(a, b, col, type, dir) {
  const av = cellText(a, col), bv = cellText(b, col);
  let cmp = 0;
  if (type === 'number') {
    cmp = parseFloat(av.replace(/[$,%]/g, '') || '0') - parseFloat(bv.replace(/[$,%]/g, '') || '0');
  } else if (type === 'date') {
    cmp = av.localeCompare(bv);
  } else if (type === 'boolean') {
    cmp = boolVal(av) - boolVal(bv);
  } else if (type === 'status') {
    cmp = (STATUS_ORDER[av.toLowerCase()] ?? 99) - (STATUS_ORDER[bv.toLowerCase()] ?? 99);
  } else {
    cmp = av.localeCompare(bv);
  }
  return cmp * dir;
}

document.querySelectorAll('th.sortable').forEach(th => {
  th.addEventListener('click', () => {
    const col = parseInt(th.dataset.col);
    const type = th.dataset.type;
    if (sortCol === col) {
      sortDir = sortDir === 1 ? -1 : sortDir === -1 ? 0 : 1;
    } else {
      sortCol = col;
      sortDir = 1;
    }
    document.querySelectorAll('.sort-chevron').forEach(c => c.textContent = '');
    const chevron = th.querySelector('.sort-chevron');
    if (chevron) chevron.textContent = sortDir === 1 ? ' \\u25b2' : sortDir === -1 ? ' \\u25bc' : '';
    const rows = sortDir === 0 ? allRows : [...allRows].sort((a, b) => compareRows(a, b, col, type, sortDir));
    rows.forEach(r => tbody.appendChild(r));
    applyFilter();
  });
});

const filterInput = document.getElementById('filter');
function applyFilter() {
  const q = filterInput.value.toLowerCase();
  let visible = 0;
  allRows.forEach(row => {
    const match = !q || row.textContent.toLowerCase().includes(q);
    row.style.display = match ? '' : 'none';
    if (match) visible++;
  });
  document.querySelector('.match-count').textContent = visible + ' of ' + allRows.length + ' rows';
}
filterInput.addEventListener('input', applyFilter);"""


def _detect_column_type(values: list[str]) -> str:
    """Return one of 'text' | 'number' | 'date' | 'boolean' | 'status' using 80% match rule."""
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


def _extract_table(content: str):
    """Return (table_lines, preamble_text, after_text), or (None, None, None) if no table."""
    lines = content.splitlines()
    table_start = table_end = None
    for i, line in enumerate(lines):
        if line.strip().startswith('|'):
            if table_start is None:
                table_start = i
            table_end = i
        elif table_start is not None:
            break
    if table_start is None:
        return None, None, None
    return (
        lines[table_start : table_end + 1],
        "\n".join(lines[:table_start]),
        "\n".join(lines[table_end + 1 :]),
    )


def _parse_table_rows(table_lines: list[str]):
    """Return (headers, data_rows) from a list of raw table lines."""

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


def _extract_post_sections(after: str) -> list[Section]:
    sections = []
    h2_re = re.compile(r'^## (.+)$', re.MULTILINE)
    matches = list(h2_re.finditer(after))
    for i, m in enumerate(matches):
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(after)
        sections.append(Section(heading=m.group(1).strip(), body_md=after[body_start:body_end].strip()))
    return sections


def parse(source_path: Path) -> Dashboard:
    """Parse a markdown source file with a primary table into a Dashboard."""
    raw_text = source_path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw_text)

    shape = post.metadata.get("render-html")
    if shape is None:
        raise ValueError(f"{source_path}: missing 'render-html' frontmatter signal")
    if shape != "dashboard":
        raise ValueError(f"{source_path}: expected render-html: dashboard, got: {shape!r}")

    options = post.metadata.get("render-html-options") or {}
    title = str(options.get("title") or source_path.stem)
    subtitle = str(options.get("subtitle") or "")
    key_column: str | None = options.get("key_column")
    column_types_override: dict[str, str] = dict(options.get("column_types") or {})

    table_lines, preamble_text, after_text = _extract_table(post.content)
    if table_lines is None:
        raise ValueError(f"{source_path}: dashboard requires a primary markdown table")

    headers, data_rows = _parse_table_rows(table_lines)
    if not headers:
        raise ValueError(f"{source_path}: dashboard requires a primary markdown table")

    columns = []
    for i, name in enumerate(headers):
        if name in column_types_override:
            col_type = str(column_types_override[name])
        else:
            col_values = [row[i] if i < len(row) else "" for row in data_rows]
            col_type = _detect_column_type(col_values)
        is_key = (name == key_column) if key_column else (i == 0)
        columns.append(Column(name=name, detected_type=col_type, is_key=is_key))

    return Dashboard(
        title=title,
        subtitle=subtitle,
        source_path=source_path,
        columns=columns,
        rows=data_rows,
        preamble_md=preamble_text.strip() if preamble_text else "",
        post_table_sections=_extract_post_sections(after_text) if after_text else [],
    )


def render(source_path: Path, options: dict | None = None) -> str:
    """Render a Dashboard as a self-contained HTML string."""
    return _render_html(parse(source_path))


def _render_html(dashboard: Dashboard) -> str:
    render_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title_esc = html.escape(dashboard.title)
    source_esc = html.escape(str(dashboard.source_path))
    n = len(dashboard.rows)

    subtitle_html = (
        f'      <div class="subtitle">{html.escape(dashboard.subtitle)}</div>\n'
        if dashboard.subtitle
        else ""
    )
    preamble_html = (
        f'\n    <section class="preamble">{render_inline_markdown(dashboard.preamble_md)}</section>'
        if dashboard.preamble_md
        else ""
    )
    thead = _render_thead(dashboard.columns)
    tbody_html = _render_tbody(dashboard.columns, dashboard.rows)
    sections_html = "".join(_render_section(s) for s in dashboard.post_table_sections)

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
{subtitle_html}      <div class="meta">{source_esc} &middot; rendered {render_date} &middot; {n} rows</div>
    </header>{preamble_html}
    <div class="filter-bar">
      <input type="search" id="filter" placeholder="Filter rows...">
      <span class="match-count">{n} rows</span>
    </div>
    <div class="table-wrap">
      <table class="dashboard">
        <thead>
{thead}
        </thead>
        <tbody>
{tbody_html}
        </tbody>
      </table>
    </div>
{sections_html}    <footer>generated by cowork-render dashboard v1 &middot; {render_date}</footer>
  </div>
  <script>{_JS}</script>
</body>
</html>"""


def _render_thead(columns: list[Column]) -> str:
    cells = "".join(
        f'            <th data-col="{i}" data-type="{col.detected_type}" class="sortable">'
        f'{html.escape(col.name)} <span class="sort-chevron"></span></th>\n'
        for i, col in enumerate(columns)
    )
    return f"          <tr>\n{cells}          </tr>"


def _render_tbody(columns: list[Column], rows: list[list[str]]) -> str:
    if not rows:
        n = len(columns)
        return f'          <tr><td colspan="{n}" style="text-align:center;color:#8b949e;padding:1rem;">No data</td></tr>'
    return "\n".join(_render_row(columns, row) for row in rows)


def _render_row(columns: list[Column], row: list[str]) -> str:
    cells = "".join(_render_cell(col, row[i] if i < len(row) else "") for i, col in enumerate(columns))
    return f"          <tr>\n{cells}          </tr>"


def _render_cell(col: Column, value: str) -> str:
    cls = _cell_class(value, col.detected_type)
    name_esc = html.escape(col.name)
    value_esc = html.escape(value)
    if cls.startswith('cell-bool-') or cls.startswith('cell-status-'):
        content = f'<span class="pill">{value_esc}</span>'
    else:
        content = value_esc
    return f'            <td class="{cls}" data-cell="{name_esc}">{content}</td>\n'


def _render_section(section: Section) -> str:
    heading_esc = html.escape(section.heading)
    body_html = render_inline_markdown(section.body_md) if section.body_md else ""
    return (
        f'    <details class="commentary-section" open>\n'
        f'      <summary>{heading_esc}</summary>\n'
        f'      <div class="commentary-body">{body_html}</div>\n'
        f'    </details>\n'
    )
