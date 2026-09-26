"""Block 4: share card (Requirement 8)."""
import io

import pytest
from PIL import Image, ImageDraw

from zine import card
from test_facts_gotn import golden_facts, needs_golden


@pytest.fixture(scope="module")
def facts():
    return golden_facts()


def _draw():
    return ImageDraw.Draw(Image.new("RGB", (10, 10)))


@needs_golden
def test_card_is_1200_by_630_png(facts):
    png = card.render(facts["25071"], "#201747", "Down 14, the Mercury found a way by 1",
                      {"value": 14, "caption": "point deficit the Mercury came back from"})
    im = Image.open(io.BytesIO(png))
    assert im.format == "PNG" and im.size == (1200, 630)


@needs_golden
def test_dropped_headline_uses_score_line(facts):
    assert card.score_headline(facts["25071"]) == "Phoenix Mercury 87, Dallas Wings 86"
    assert card.score_headline(facts["25014"]).endswith(", in overtime")


@pytest.mark.parametrize("text", [
    "Short",
    "Down 14, the Mercury found a way by 1",
    "A very long headline that keeps going well past what fits on two lines of the card and then keeps going more and more and more",
    "Supercalifragilisticexpialidocious" * 4,
])
def test_fit_never_overflows(text):
    d = _draw()
    font, lines = card.fit(d, text.upper(), card.SLAB, 1060, 2, 44, 26)
    assert 1 <= len(lines) <= 2
    assert all(card._width(d, l, font) <= 1060 for l in lines)


def test_ellipsis_only_at_the_floor():
    d = _draw()
    font, lines = card.fit(d, "DOWN 14, THE MERCURY FOUND A WAY BY 1", card.SLAB, 1060, 2, 44, 26)
    assert font.size == 44 and not any(l.endswith(card.ELLIPSIS) for l in lines)
    font, lines = card.fit(d, "WORD " * 200, card.SLAB, 1060, 2, 44, 26)
    assert font.size == 26 and lines[-1].endswith(card.ELLIPSIS)


@needs_golden
@pytest.mark.parametrize("spot", ["#FFFFFF", "#CFE8EF", "#C8102E", "#201747", "#B896D4"])
def test_any_team_color_renders(facts, spot):
    assert card.render(facts["25014"], spot, None, None)[:8] == b"\x89PNG\r\n\x1a\n"
