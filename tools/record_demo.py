"""record_demo.py - drive the live site from a shot list and save a video. Dev tool only,
never part of the Lambda bundle.

Usage (PowerShell, from the repo folder):
    pip install playwright
    python -m playwright install chromium
    python tools/record_demo.py demo/demo_shots.json --out demo/demo.mp4

Without ffmpeg on the machine it saves demo/demo.webm instead (Claude converts it).
Actions: goto, click, hover, press, wait, wait_for, scroll (smooth, by y), scroll_to (selector),
media (print | screen), play (an <audio> selector). Every step takes an optional "pause" in ms (default 600).
"""
import argparse
import asyncio
import json
import pathlib
import shutil
import subprocess
import sys
from urllib.parse import urljoin

from playwright.async_api import async_playwright


async def run(shots, headed, w, h):
    raw_dir = pathlib.Path("demo_raw")
    raw_dir.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not headed, args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"])
        ctx = await browser.new_context(viewport={"width": w, "height": h}, record_video_dir=str(raw_dir),
                                        record_video_size={"width": w, "height": h})
        page = await ctx.new_page()
        try:
            await page.goto(shots["url"], wait_until="networkidle", timeout=45000)
            await page.wait_for_timeout(1500)
            for i, s in enumerate(shots["steps"]):
                a = s["action"]
                try:
                    if a == "goto":
                        await page.goto(urljoin(shots["url"], s["path"]), wait_until="networkidle", timeout=45000)
                    elif a == "click":
                        await page.click(s["selector"], timeout=10000)
                        await page.wait_for_load_state("networkidle")
                    elif a == "hover":
                        await page.hover(s["selector"], timeout=10000)
                    elif a == "press":
                        await page.keyboard.press(s["key"])
                    elif a == "wait":
                        await page.wait_for_timeout(s["ms"])
                    elif a == "wait_for":
                        await page.wait_for_selector(s["selector"], timeout=s.get("ms", 30000))
                    elif a == "scroll":
                        await page.evaluate("y => window.scrollBy({top: y, behavior: 'smooth'})", s.get("y", 600))
                    elif a == "scroll_to":
                        await page.wait_for_selector(s["selector"], timeout=10000)
                        await page.evaluate(
                            "([sel, off]) => { const el = document.querySelector(sel);"
                            " window.scrollTo({top: el.getBoundingClientRect().top + window.scrollY - off, behavior: 'smooth'}); }",
                            [s["selector"], s.get("offset", 90)])
                    elif a == "play":  # starts the player so its progress bar moves on camera (the video is silent)
                        await page.evaluate("sel => document.querySelector(sel).play()", s["selector"])
                    elif a == "media":
                        await page.emulate_media(media=s["value"])
                        await page.evaluate("window.scrollTo(0, 0)")
                    else:
                        raise ValueError("unknown action '%s'" % a)
                except Exception as e:
                    print("FAIL at step %d (%s): %s" % (i, a, e), file=sys.stderr)
                    await page.screenshot(path="demo_fail_step%d.png" % i)
                    raise
                await page.wait_for_timeout(s.get("pause", 600))
            await page.wait_for_timeout(2500)
        finally:
            video = page.video
            await ctx.close()
            await browser.close()
    return pathlib.Path(await video.path())


def finish(raw, out, speed):
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not shutil.which("ffmpeg"):
        final = out.with_suffix(".webm")
        shutil.move(str(raw), final)
        print("ffmpeg not found, saved WebM instead: %s" % final)
        return final
    vf = ("setpts=PTS/%s," % speed) if speed != 1.0 else ""
    # -ss trims the blank white frames before the first page paints
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "2", "-i", str(raw), "-vf", vf + "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                    "-c:v", "libx264", "-crf", "22", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-an", str(out)], check=True)
    raw.unlink()
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("shotlist")
    ap.add_argument("--out", default="demo/demo.mp4")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    a = ap.parse_args()
    shots = json.loads(pathlib.Path(a.shotlist).read_text(encoding="utf-8"))
    raw = asyncio.run(run(shots, a.headed, a.width, a.height))
    final = finish(raw, a.out, a.speed)
    print("SUCCESS: %s (%d KB)" % (final, final.stat().st_size // 1024))
