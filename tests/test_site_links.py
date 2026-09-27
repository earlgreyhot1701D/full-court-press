"""Every relative link and asset on every page of the built site resolves to a real file."""
import os
import re

from zine import dev_render_golden, site_build
from zine.store import LocalStore
from test_facts_gotn import needs_golden


@needs_golden
def test_no_broken_links(tmp_path, monkeypatch):
    monkeypatch.setattr(site_build, "GOLDEN_AT", "")
    files, _ = dev_render_golden.golden_files(dev_render_golden.standin_result)
    files.update(site_build.static_files())
    store = LocalStore(str(tmp_path))
    for path, (body, _t) in files.items():
        store.put(path, body)
    bad, n = [], 0
    for path, (body, ctype) in files.items():
        if not ctype.startswith("text/html"):
            continue
        here = os.path.dirname(os.path.join(str(tmp_path), path))
        for u in re.findall(r'(?:href|src|content)="([^"#]+)"', body.decode("utf-8")):
            if u.startswith(("http", "mailto", "data:")) or not re.search(r"\.(html|css|js|png|svg|mp3|ttf|json)$", u):
                continue
            n += 1
            if not os.path.exists(os.path.normpath(os.path.join(here, u))):
                bad.append((path, u))
    assert n > 300 and not bad, bad[:5]


@needs_golden
def test_pages_need_nothing_the_csp_blocks():
    """template.yaml's CSP: no inline <style> or <script>, no outside hosts for assets."""
    import re as _re
    files, _ = dev_render_golden.golden_files(dev_render_golden.standin_result)
    for path, (body, ctype) in files.items():
        if ctype.startswith("text/html"):
            html = body.decode("utf-8")
            assert "<style" not in html, path
            assert not _re.search(r"<script(?![^>]*\bsrc=)", html), path
            assert not _re.search(r'src="https?://', html), path                   # nothing loaded from outside
            assert not _re.search(r'<link[^>]*href="https?://', html), path       # no outside stylesheets


@needs_golden
def test_every_page_has_icon_and_one_social_preview(monkeypatch):
    """Favicon links on every page; exactly one og:image per page. Issue pages use their own
    share card; every other page uses the default preview, absolute when SITE_URL is set."""
    monkeypatch.setenv("SITE_URL", "https://example.test/")
    files, _ = dev_render_golden.golden_files(dev_render_golden.standin_result)
    assert "static/favicon.svg" in site_build.static_files()
    pages = {p: b.decode("utf-8") for p, (b, t) in files.items() if t.startswith("text/html")}
    assert pages
    for path, html in pages.items():
        assert 'rel="icon"' in html and "favicon.svg" in html, path
        imgs = re.findall(r'property="og:image" content="([^"]*)"', html)
        assert len(imgs) == 1, (path, imgs)
        if imgs[0].endswith("card.png"):
            continue
        assert imgs[0] == "https://example.test/static/og-default.png", (path, imgs[0])


def test_front_page_names_the_date_not_last_night():
    """The slate heading is the games' date. "Last night" is wrong the moment the page is read a day later."""
    nights = {"2026-09-24": [], "2026-09-21": []}
    files = site_build.front_files(nights)
    front = files["index.html"][0].decode("utf-8")
    assert '<h2 class="slab">THURSDAY, SEP 24</h2>' in front
    assert "Last night</h2>" not in front
    assert "<title>Full Court Press . WNBA Thursday, Sep 24</title>" in front
    night = files["archive/2026-09-21/index.html"][0].decode("utf-8")
    assert '<h2 class="slab">MONDAY, SEP 21</h2>' in night


@needs_golden
def test_golden_front_says_what_it_is_and_dates_every_card(monkeypatch):
    """The golden set mixes nights: no "last night", no "Game of the Night", a date on every card."""
    monkeypatch.setattr(site_build, "GOLDEN_AT", "")
    files, _ = dev_render_golden.golden_files(dev_render_golden.standin_result)
    front = files["index.html"][0].decode("utf-8")
    assert '<h2 class="slab">The golden set</h2>' in front
    assert "5 real games, Aug 16 to Sep 21" in front
    assert front.count('class="gdate"') == 5
    assert "Game of the Night" not in front and "Pick of the Set" in front
    assert 'class="golden-intro"' in front
