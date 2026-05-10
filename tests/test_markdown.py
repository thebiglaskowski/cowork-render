"""Tests for the shared markdown rendering helpers in cowork_render._markdown."""

from cowork_render._markdown import render_block, render_inline


# --- render_inline ---

def test_render_inline_preserves_code_span_content():
    result = render_inline("`[text](url)`")
    assert "<code>[text](url)</code>" in result
    assert "<a href" not in result


def test_render_inline_handles_bold_italic_code_link():
    result = render_inline("**bold** *italic* `code` [label](http://example.com)")
    assert "<strong>bold</strong>" in result
    assert "<em>italic</em>" in result
    assert "<code>code</code>" in result
    assert '<a href="http://example.com">label</a>' in result


def test_render_inline_no_paragraph_wrapper():
    result = render_inline("plain text")
    assert "<p>" not in result
    assert result.strip() == "plain text"


def test_render_inline_escapes_raw_html():
    result = render_inline("<script>alert(1)</script>")
    assert "&lt;script&gt;" in result
    assert "<script>" not in result


# --- render_block ---

def test_render_block_produces_paragraphs():
    result = render_block("First paragraph.\n\nSecond paragraph.")
    assert result.count("<p>") == 2
    assert "First paragraph." in result
    assert "Second paragraph." in result


def test_render_block_handles_bullet_lists():
    result = render_block("- item one\n- item two")
    assert "<ul>" in result
    assert "<li>" in result
    assert "item one" in result
    assert "item two" in result


def test_render_block_handles_fenced_code_blocks():
    result = render_block("```bash\necho hello\n```")
    assert "<pre>" in result
    assert "<code" in result
    assert "echo hello" in result


def test_render_block_handles_blockquotes():
    result = render_block("> quoted text")
    assert "<blockquote>" in result
    assert "quoted text" in result


def test_render_block_escapes_raw_html():
    result = render_block("<script>alert(1)</script>")
    assert "&lt;script&gt;" in result
    assert "<script>" not in result
