"""Tests for ASCII diagram detection and rendering."""

from cowork_render._markdown import render_block
from cowork_render.diagrams import _render_flow_horizontal, _render_flow_vertical, _render_tree, render_diagram


_TREE_BASIC = """\
Root
├ Child A
└ Child B
"""

_TREE_DEEP = """\
Root
├ Child A
│  ├ Grandchild 1
│  └ Grandchild 2
└ Child B
"""

_FLOW_V_BASIC = """\
Automation Engine
↓
Digital Assets
↓
Revenue Streams
↓
Portfolio Growth
"""

_FLOW_H_BASIC = "Step One → Step Two → Step Three"

_FLOW_H_MULTILINE = "Step One → Step Two → Step Three\n→ Step Four → Step Five"


def test_tree_basic_returns_diagram_html():
    result = _render_tree(_TREE_BASIC)
    assert result is not None
    assert '<ul class="diagram-tree">' in result
    assert '<li>Root' in result
    assert '<li>Child A' in result
    assert '<li>Child B' in result


def test_tree_depth_hierarchy_nests_uls():
    result = _render_tree(_TREE_DEEP)
    assert result is not None
    assert '<ul class="diagram-tree">' in result
    # Grandchildren should appear in nested <ul>
    assert '<ul>' in result
    assert 'Grandchild 1' in result
    assert 'Grandchild 2' in result


def test_tree_non_match_returns_none():
    result = _render_tree("Some text\nwith no tree markers\njust plain lines")
    assert result is None


def test_tree_single_marker_line_returns_none():
    # Only 1 line with a tree marker — below the 2-marker threshold
    result = _render_tree("Root\n├ Only Child\nPlain line")
    # "├ Only Child" has a marker, "Root" has none, "Plain line" has none → only 1 marker line
    assert result is None


def test_flow_vertical_basic():
    result = _render_flow_vertical(_FLOW_V_BASIC)
    assert result is not None
    assert '<div class="diagram-flow-v">' in result
    assert result.count('<div class="flow-step">') == 4
    assert 'Automation Engine' in result
    assert 'Portfolio Growth' in result


def test_flow_vertical_non_match_single_arrow():
    content = "Step One\n↓\nStep Two"
    result = _render_flow_vertical(content)
    # Only 1 ↓ → below the 2-arrow threshold
    assert result is None


def test_flow_horizontal_basic():
    result = _render_flow_horizontal(_FLOW_H_BASIC)
    assert result is not None
    assert '<div class="diagram-flow-h">' in result
    assert result.count('<div class="flow-step">') == 3
    assert result.count('<div class="flow-arrow"') == 2
    assert 'Step One' in result
    assert 'Step Three' in result


def test_flow_horizontal_multiline_joins():
    result = _render_flow_horizontal(_FLOW_H_MULTILINE)
    assert result is not None
    assert '<div class="diagram-flow-h">' in result
    assert result.count('<div class="flow-step">') == 5


def test_opt_out_noformat_returns_none():
    # Even content that would match tree detection should be skipped with noformat lang
    result = render_diagram(_TREE_BASIC, fence_lang='noformat')
    assert result is None


def test_opt_out_plain_returns_none():
    result = render_diagram(_FLOW_V_BASIC, fence_lang='plain')
    assert result is None


def test_html_escape_in_labels():
    content = "Root\n├ <script>alert(1)</script>\n└ Normal & safe"
    result = render_diagram(content)
    assert result is not None
    assert '<script>' not in result
    assert '&lt;script&gt;' in result
    assert '&amp;' in result


def test_detection_order_tree_wins_over_flow():
    # Content with tree markers AND ↓ — tree should match first
    content = "Root\n├ Step A\n↓\n└ Step B"
    result = render_diagram(content)
    assert result is not None
    assert '<ul class="diagram-tree">' in result
    assert 'diagram-flow-v' not in result


def test_integration_render_block_tree_diagram():
    md = "Before\n\n```\nRoot\n├ Child A\n└ Child B\n```\n\nAfter"
    result = render_block(md)
    # Diagram replaces <pre><code>
    assert '<ul class="diagram-tree">' in result
    assert '<pre><code>' not in result
    assert 'code-block-wrapper' not in result


def test_integration_non_diagram_code_block_preserved():
    md = "```bash\necho hello\n```"
    result = render_block(md)
    # Non-diagram block gets the copy-button wrapper, not a diagram
    assert 'code-block-wrapper' in result
    assert '<pre><code class="language-bash">' in result
    assert 'diagram' not in result
