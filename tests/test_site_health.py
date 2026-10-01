"""The product promise, end to end: every game in the golden set publishes a usable issue.

Built twice through the same site builder the morning run uses:
  saved voices  the AI writing as it was kept
  all failed    every AI voice cut, the worst night the checks can produce
Either way, every edition must have a story (an AI recap or the labeled code recap), its share
card, and every file the page asks for. Links are covered by test_site_links.test_no_broken_links.
"""
import re

import pytest

from zine import dev_render_golden, site_build
from zine.voices import VOICE_ORDER
from test_facts_gotn import needs_golden

STORY = re.compile(r'<p class="recap( plainrecap)?">([^<]+)</p>')


def build(result_fn):
    files, _ = dev_render_golden.golden_files(result_fn)
    files.update(site_build.static_files())
    return files


@needs_golden
@pytest.mark.parametrize("mode", ["saved voices", "all failed"])
def test_every_edition_publishes_a_usable_issue(monkeypatch, mode):
    monkeypatch.setattr(site_build, "GOLDEN_AT", "")
    files = build(dev_render_golden.standin_result if mode == "saved voices" else (lambda f, ed, v: None))
    facts = dev_render_golden.load_all()
    assert len(facts) == 5
    stories = {"ai": 0, "code": 0}
    for f in facts:
        for team in (f["home"], f["away"]):
            folder = "wnba/%s/%s/%s/" % (f["date_local"], f["game_id"], team["abbrev"])
            assert folder + "card.png" in files and len(files[folder + "card.png"][0]) > 1000, folder
            for v in VOICE_ORDER:
                path = folder + ("index.html" if v == "the_call" else "film-room/index.html")
                assert path in files, path
                html = files[path][0].decode("utf-8")
                m = STORY.search(html)
                assert m and len(m.group(2).strip()) > 40, ("empty story area", path)
                assert "recap writersroom" not in html, ("writers' room with no story under it", path)
                stories["code" if m.group(1) else "ai"] += 1
                # every local file the page asks for exists in the build
                here = path.rsplit("/", 1)[0]
                for ref in re.findall(r'(?:href|src)="([^"#?]+\.(?:css|js|png|svg|ttf))"', html):
                    if ref.startswith("http"):
                        continue
                    parts = (here + "/" + ref).split("/")
                    norm = []
                    for p in parts:
                        norm.pop() if p == ".." else (p and p != "." and norm.append(p))
                    assert "/".join(norm) in files, (path, ref)
    assert sum(stories.values()) == 20  # 5 games x 2 editions x 2 voices
    if mode == "all failed":
        assert stories == {"ai": 0, "code": 20}


@needs_golden
def test_front_page_lists_every_game():
    files, _ = dev_render_golden.golden_files(dev_render_golden.standin_result)
    front = files["index.html"][0].decode("utf-8")
    assert front.count('<article class="card') == 5
