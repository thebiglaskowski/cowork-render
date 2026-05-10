"""WCAG AA contrast test — every defined text-on-background pair must pass 4.5:1."""

from __future__ import annotations

import pytest

from cowork_render.theme import all_text_on_bg_pairs


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        v = c / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    l1 = _relative_luminance(_hex_to_rgb(fg_hex))
    l2 = _relative_luminance(_hex_to_rgb(bg_hex))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize("text_token,text_hex,bg_token,bg_hex", all_text_on_bg_pairs())
def test_text_on_bg_passes_wcag_aa(text_token, text_hex, bg_token, bg_hex):
    """Every text/bg pair defined in theme must have >=4.5:1 contrast (WCAG AA normal text)."""
    ratio = _contrast_ratio(text_hex, bg_hex)
    assert ratio >= 4.5, (
        f"Contrast {ratio:.2f}:1 fails WCAG AA for {text_token} ({text_hex}) "
        f"on {bg_token} ({bg_hex}). Minimum is 4.5:1."
    )
