"""Task 1.1 verification: every character used by team names and abbreviations
must have a glyph in BOTH self-hosted fonts, so nothing falls back to a system
font. Stdlib-only TrueType cmap reader (no third-party dependency).

Run: python -m pytest tests/test_font_glyph_coverage.py
"""
import json
import os
import struct

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(ROOT, "static", "fonts")
COLORS = os.path.join(ROOT, "static", "team_colors.json")

ALFA = os.path.join(FONTS, "AlfaSlabOne-Regular.ttf")
ARCHIVO = os.path.join(FONTS, "Archivo-VariableFont_wdth_wght.ttf")


def _read_cmap_codepoints(path):
    """Return the set of Unicode codepoints the font's cmap can map."""
    with open(path, "rb") as f:
        data = f.read()

    # offset table
    sfnt, num_tables = struct.unpack(">4sH", data[0:6])
    # skip searchRange/entrySelector/rangeShift (6 bytes)
    rec = 12
    cmap_off = None
    for _ in range(num_tables):
        tag, _checksum, off, _length = struct.unpack(">4sIII", data[rec:rec + 16])
        if tag == b"cmap":
            cmap_off = off
        rec += 16
    if cmap_off is None:
        return set()

    _version, n_sub = struct.unpack(">HH", data[cmap_off:cmap_off + 4])
    best = None  # prefer a Unicode subtable (format 12 > 4)
    subs = []
    p = cmap_off + 4
    for _ in range(n_sub):
        plat, enc, sub_off = struct.unpack(">HHI", data[p:p + 8])
        subs.append((plat, enc, cmap_off + sub_off))
        p += 8

    codepoints = set()
    for plat, enc, off in subs:
        fmt = struct.unpack(">H", data[off:off + 2])[0]
        if fmt == 4:
            (_fmt, _len, _lang, segx2) = struct.unpack(">HHHH", data[off:off + 8])
            segc = segx2 // 2
            base = off + 14
            end = struct.unpack(">%dH" % segc, data[base:base + segx2])
            base += segx2 + 2  # +2 reservedPad
            start = struct.unpack(">%dH" % segc, data[base:base + segx2])
            base += segx2
            delta = struct.unpack(">%dH" % segc, data[base:base + segx2])
            base += segx2
            id_range_base = base
            id_range = struct.unpack(">%dH" % segc, data[base:base + segx2])
            for i in range(segc):
                s, e, d, ro = start[i], end[i], delta[i], id_range[i]
                if s == 0xFFFF:
                    continue
                for c in range(s, e + 1):
                    if ro == 0:
                        g = (c + d) & 0xFFFF
                    else:
                        gi = id_range_base + i * 2 + ro + (c - s) * 2
                        if gi + 2 > len(data):
                            continue
                        g = struct.unpack(">H", data[gi:gi + 2])[0]
                        if g != 0:
                            g = (g + d) & 0xFFFF
                    if g != 0:
                        codepoints.add(c)
        elif fmt == 12:
            (_fmt, _res, _len, _lang, ngroups) = struct.unpack(">HHIII", data[off:off + 16])
            gp = off + 16
            for _ in range(ngroups):
                sc, ec, _sg = struct.unpack(">III", data[gp:gp + 12])
                for c in range(sc, ec + 1):
                    codepoints.add(c)
                gp += 12
    return codepoints


def _needed_chars():
    with open(COLORS, encoding="utf-8") as f:
        teams = json.load(f)["teams"]
    text = ""
    for abbr, info in teams.items():
        text += abbr + info["team"]
    return set(text)


def test_both_fonts_exist():
    assert os.path.getsize(ALFA) > 0
    assert os.path.getsize(ARCHIVO) > 0


def test_every_team_char_has_a_glyph_in_both_fonts():
    needed = _needed_chars()
    alfa = _read_cmap_codepoints(ALFA)
    archivo = _read_cmap_codepoints(ARCHIVO)
    missing_alfa = sorted(ch for ch in needed if ord(ch) not in alfa)
    missing_archivo = sorted(ch for ch in needed if ord(ch) not in archivo)
    assert not missing_alfa, f"Alfa Slab One missing glyphs for: {missing_alfa}"
    assert not missing_archivo, f"Archivo missing glyphs for: {missing_archivo}"


if __name__ == "__main__":
    needed = _needed_chars()
    alfa = _read_cmap_codepoints(ALFA)
    archivo = _read_cmap_codepoints(ARCHIVO)
    ma = sorted(ch for ch in needed if ord(ch) not in alfa)
    mr = sorted(ch for ch in needed if ord(ch) not in archivo)
    print(f"needed distinct chars: {len(needed)}")
    print(f"Alfa cmap size: {len(alfa)}  Archivo cmap size: {len(archivo)}")
    print(f"missing in Alfa: {ma}")
    print(f"missing in Archivo: {mr}")
    print("PASS" if not ma and not mr else "FAIL")


CAVEAT = os.path.join(FONTS, "Caveat-VariableFont_wght.ttf")


def test_margin_notes_only_use_characters_caveat_has():
    """Zine-energy margin notes (approved Sep 24). Every character of every note's text must be in
    Caveat, or it silently falls back to another font. Arrows are inline SVG for that reason."""
    import re
    tpl = open(os.path.join(ROOT, "templates", "issue.html"), encoding="utf-8").read()
    notes = re.findall(r'class="scribble[^"]*"[^>]*>(.*?)</(?:span|div)>\s*(?:<div class="gotn"|{%|$|\n)', tpl, re.S)
    texts = [re.sub(r"<svg.*?</svg>", "", n, flags=re.S) for n in notes]
    texts = [re.sub(r"<[^>]+>|&[a-z]+;", "", n).strip() for n in texts]
    assert texts, "no margin notes found in the template"
    have = _read_cmap_codepoints(CAVEAT)
    missing = sorted({c for s in texts for c in s if ord(c) not in have and not c.isspace()})
    assert not missing, missing
