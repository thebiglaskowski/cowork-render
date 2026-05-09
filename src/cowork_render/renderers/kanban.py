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
.card-body { font-size: 0.8rem; color: #8b949e; margin-top: 0.25rem; line-height: 1.4; white-space: pre-wrap; }
.no-cards { color: #8b949e; font-size: 0.8rem; font-style: italic; text-align: center; padding: 0.5rem 0; }
footer { margin-top: 1.5rem; font-size: 0.75rem; color: #8b949e; font-family: 'SF Mono', Menlo, Consolas, monospace; }
#export-fallback { width: 100%; margin-top: 0.5rem; background: #1f2128; color: #e1e4e8; border: 1px solid #2d3138; padding: 0.5rem; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.8rem; height: 200px; }
@media (max-width: 600px) { .board { grid-template-columns: 1fr; } }"""

# Plain string (not f-string) — JS braces need no escaping here.
# __FM_JSON__ and __PREAMBLE_JSON__ are replaced at render time via .replace().
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
    allowed_columns: list[str] | None = options.get("columns") or None
    title: str = options.get("title") or source_path.stem

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


def _json_script_safe(value: str) -> str:
    """json.dumps + escape < so </script> cannot break out of the script block."""
    return json.dumps(value).replace("<", "\\u003c")


def _render_html(board: Board) -> str:
    render_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fm_json = _json_script_safe(board.raw_frontmatter)
    preamble_json = _json_script_safe(board.raw_preamble)
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
        f'            <h3 class="card-title">{html.escape(card.title)}</h3>{body}\n'
        f"          </article>"
    )
