"""contrast.py (pure) . decide the text colour that sits on a team's spot colour,
at render time, never in JavaScript (design/RENDER-CONTRAST.md).

WCAG 2.x relative luminance and contrast ratio. No dependency, no I/O.
"""

PAPER = "#F4EEE2"
INK = "#1E1B18"
MIN_RATIO = 4.5  # WCAG AA for normal text


def _hex_to_rgb(hexstr):
    h = hexstr.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _channel(c):
    # c is 0..255; WCAG linearization
    s = c / 255.0
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(hexstr):
    r, g, b = _hex_to_rgb(hexstr)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(hex_a, hex_b):
    la = relative_luminance(hex_a)
    lb = relative_luminance(hex_b)
    lighter, darker = (la, lb) if la >= lb else (lb, la)
    return (lighter + 0.05) / (darker + 0.05)


def on_spot(spot_hex, paper=PAPER, ink=INK, min_ratio=MIN_RATIO):
    """Return (text, ratio, low_contrast) for text sitting on `spot_hex`.

    text is "paper" or "ink", whichever has the higher contrast against the spot
    colour. low_contrast is True when even the winner is below min_ratio, in which
    case the caller also emits data-lowc="1" so the .spot-surface escape hatch
    pulls text off the colour entirely.
    """
    paper_ratio = contrast_ratio(spot_hex, paper)
    ink_ratio = contrast_ratio(spot_hex, ink)
    if paper_ratio >= ink_ratio:
        return "paper", round(paper_ratio, 1), paper_ratio < min_ratio
    return "ink", round(ink_ratio, 1), ink_ratio < min_ratio
