"""Tests for the theme loader in cowork_render.theme."""

import pytest

from cowork_render.theme import _kebab_case, _load_design, color, get_theme_css


def test_design_loads_with_required_keys():
    design = _load_design()
    assert "colors" in design
    assert "typography" in design
    assert "rounded" in design
    assert "spacing" in design


def test_get_theme_css_structure():
    css = get_theme_css()
    assert css.startswith(":root {")
    assert css.strip().endswith("}")
    assert "--bg-base:" in css
    assert "--text-base:" in css
    assert "--severity-high:" in css


def test_color_returns_hex_for_known_token():
    assert color("bg-base") == "#0d1117"


def test_color_raises_for_unknown_token():
    with pytest.raises(KeyError):
        color("nonexistent")


def test_kebab_case_camel():
    assert _kebab_case("fontFamily") == "font-family"


def test_kebab_case_multi_word():
    assert _kebab_case("camelCase") == "camel-case"


def test_kebab_case_already_simple():
    assert _kebab_case("simple") == "simple"


def test_theme_css_includes_jetbrains_mono():
    css = get_theme_css()
    assert "JetBrains Mono" in css


def test_theme_css_includes_body_font_size_17px():
    css = get_theme_css()
    assert "17px" in css
