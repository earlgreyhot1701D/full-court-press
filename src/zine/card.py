"""Share card: one 1200x630 PNG per edition (Requirement 8). Pure: no network, no model.

Every word on the card is deterministic or fact-locked: team names and scores from the facts
sheet, the date, The Number (value and caption from the facts sheet), and the headline, which is
the locked headline of the default voice or, if that was dropped, a score line built by code.
No logos, no photos, no league marks.

Text fitting (Req 8.3): the headline may wrap to 2 lines; if it still does not fit it shrinks
toward a floor size, and only at the floor does the last line end in an ellipsis. Nothing
ever overflows its box.

Reference layout: design/card-mercury.png, design/card-stress.png (Sep 20 proof).
"""
import io
import os
from datetime import date

from PIL import Image, ImageDraw, ImageFont

from zine import contrast
from zine.paths import STATIC

W, H = 1200, 630
FONTS = os.path.join(STATIC, "fonts")
SLAB = os.path.join(FONTS, "AlfaSlabOne-Regular.ttf")
SANS = os.path.join(FONTS, "Archivo-VariableFont_wdth_wght.ttf")

PAPER, INK, MUT, CARD = "#F4EEE2", "#1E1B18", "#6B6259", "#FFFBF3"
RULE = "#E4DCCD"
PINK = "#FF48B0"
ELLIPSIS = "…"


def _font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight, 100])  # Archivo axes, in font order: Weight, Width
        except (OSError, ValueError):
            pass
    return f


def _width(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def _wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if not cur or _width(draw, trial, font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _ellipsize(draw, line, font, max_w):
    while line and _width(draw, line + ELLIPSIS, font) > max_w:
        line = line[:-1].rstrip()
    return line + ELLIPSIS


def fit(draw, text, path, max_w, max_lines, start, floor, weight=None):
    """-> (font, lines). Shrinks from `start` to `floor`; ellipsis only at the floor.
    Every returned line is at most max_w wide."""
    size = start
    while True:
        font = _font(path, size, weight)
        lines = _wrap(draw, text, font, max_w)
        if len(lines) <= max_lines and all(_width(draw, l, font) <= max_w for l in lines):
            return font, lines
        if size <= floor:
            kept = lines[:max_lines]
            if len(lines) > max_lines:  # text was cut: say so on the last kept line
                kept[-1] = _ellipsize(draw, kept[-1], font, max_w)
            kept = [l if _width(draw, l, font) <= max_w else _ellipsize(draw, l, font, max_w) for l in kept]
            return font, kept
        size -= 2


def score_headline(f):
    """Req 8.2: the headline when the voice's headline was dropped."""
    w, l = (f["home"], f["away"]) if f["winner_abbrev"] == f["home"]["abbrev"] else (f["away"], f["home"])
    s = "%s %d, %s %d" % (w["team"], w["score"], l["team"], l["score"])
    return s + (", in overtime" if f.get("overtime_periods") else "")


def _nickname(team):
    """"Phoenix Mercury" -> "MERCURY"."""
    return team["team"].split()[-1].upper()


def _date_line(f):
    d = date.fromisoformat(f["date_local"])
    return "%s . %s %s %d %d" % (f.get("league", "wnba").upper(), d.strftime("%a").upper(),
                                 d.strftime("%b").upper(), d.day, d.year)


def render(f, spot, headline=None, number=None):
    """-> PNG bytes. `spot` is the edition team's hex color; `headline` is the locked headline
    or None; `number` is {"value", "caption"} from voice_view.the_number, or None."""
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    for y in range(156, H, 26):  # ruled paper
        d.line([(0, y), (W, y)], fill=RULE, width=1)

    # top band: masthead, date, team-color rule
    d.rectangle([0, 0, W, 120], fill=INK)
    d.text((44, 38), "FULL COURT PRESS", font=_font(SLAB, 48), fill=PAPER)
    dl = _date_line(f)
    df = _font(SANS, 20, 700)
    d.text((W - 44 - _width(d, dl, df), 56), dl, font=df, fill=PAPER)
    d.rectangle([0, 120, W, 130], fill=spot)

    # score block: winner in ink over loser in muted, status above
    w, l = (f["home"], f["away"]) if f["winner_abbrev"] == f["home"]["abbrev"] else (f["away"], f["home"])
    status = "FINAL / OT" if f.get("overtime_periods") else "FINAL"
    d.text((44, 150), status, font=_font(SANS, 18, 800), fill=MUT)
    for i, (team, color) in enumerate(((w, INK), (l, MUT))):
        y = 178 + i * 86
        sf = _font(SLAB, 72)
        score = str(team["score"])
        sw = _width(d, score, sf)
        name_font, name_lines = fit(d, _nickname(team), SLAB, 700 - 44 - sw - 30, 1, 72, 40)
        d.text((44, y + (72 - name_font.size) // 2), name_lines[0], font=name_font, fill=color)
        d.text((700 - sw, y), score, font=sf, fill=color)

    # The Number tile: caption sits at the bottom, the number takes the space above it
    if number:
        d.rectangle([768, 166, 1164, 352], fill=spot)
        d.rectangle([760, 158, 1156, 344], fill=CARD, outline=INK, width=4)
        d.text((783, 176), "THE NUMBER", font=_font(SANS, 18, 800), fill=MUT)
        cap_top = 326
        if number.get("caption"):
            cf, cl = fit(d, number["caption"], SANS, 352, 2, 20, 14, 600)
            cap_top = 326 - len(cl) * (cf.size + 4)
            for j, line in enumerate(cl):
                d.text((783, cap_top + j * (cf.size + 4)), line, font=cf, fill=MUT)
        room = cap_top - 8 - 204  # from under the label to over the caption
        size = 96
        while size > 40:
            nf = _font(SLAB, size)
            top, bottom = d.textbbox((0, 0), str(number["value"]), font=nf, anchor="ls")[1::2]
            if -top <= room and _width(d, str(number["value"]), nf) <= 350:
                break
            size -= 4
        d.text((780, cap_top - 8), str(number["value"]), font=nf, fill=INK, anchor="ls")

    # headline block in the edition team's color; if no text color reaches 4.5:1 on it,
    # the block goes to paper and the team color stays on the border and shadow only
    text_on, _ratio, low = contrast.on_spot(spot)
    fill = CARD if low else spot
    ink = INK if low or text_on == "ink" else PAPER
    d.rectangle([52, 382, 1164, 546], fill=INK)  # hard shadow
    d.rectangle([44, 374, 1156, 538], fill=fill, outline=spot if low else INK, width=6 if low else 4)
    hf, hl = fit(d, (headline or score_headline(f)).upper(), SLAB, 1060, 2, 44, 26)
    lh = hf.size + 10
    top = 374 + (164 - lh * len(hl)) // 2
    for j, line in enumerate(hl):
        d.text((68, top + j * lh), line, font=hf, fill=ink)

    # footer
    d.text((44, 574), "FULL COURT PRESS . UNOFFICIAL FAN ZINE", font=_font(SANS, 18, 800), fill=MUT)
    d.rectangle([W - 44 - 60, 580, W - 44, 590], fill=PINK)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
