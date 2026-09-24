"""Block 0 spike 0.6: does Pillow plus a bundled TTF run in Lambda?

Throwaway. Renders a 1200x630 PNG with one line of text in the bundled TTF,
returns the byte size of the PNG. No S3, no network.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = os.path.join(os.path.dirname(__file__), "AlfaSlabOne-Regular.ttf")


def handler(event, context):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (11, 61, 46))  # deep green background
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(FONT_PATH, 96)
        font_ok = True
    except Exception as e:
        font = ImageFont.load_default()
        font_ok = False
        return {"font_loaded": font_ok, "error": repr(e)}

    text = "FULL COURT PRESS"
    # center the line
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W - tw) / 2 - bbox[0], (H - th) / 2 - bbox[1]), text, font=font, fill=(240, 240, 240))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png = buf.getvalue()

    return {
        "font_loaded": font_ok,
        "png_bytes": len(png),
        "size": [W, H],
        "pillow_version": getattr(__import__("PIL"), "__version__", "unknown"),
    }
