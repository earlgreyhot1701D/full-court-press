"""Every optional part of the facts sheet can be missing or empty and the pages, card and audio
still build. Found on the live stack Sep 26: game 25079 had no `quarters` (they did not add up),
and the issue template assumed they were always there."""
import copy

import pytest

from zine import audio_script, site_build
from test_facts_gotn import golden_facts, needs_golden

CORE = {"game_id", "league", "date_local", "home", "away", "winner_abbrev", "numbers", "number_labels",
        "the_number_key", "allowed_numbers", "allowed_names", "tip_time_utc", "season", "season_type", "status"}


@needs_golden
@pytest.mark.parametrize("variant", ["missing", "empty"])
def test_pages_survive_any_optional_fact_missing(variant):
    for gid, f in golden_facts().items():
        for key in [k for k in f if k not in CORE]:
            g = copy.deepcopy(f)
            if variant == "missing":
                g.pop(key)
            else:
                v = g[key]
                g[key] = type(v)() if isinstance(v, (list, dict, str)) else None
            rows = [site_build.slate_row(g, g["game_id"])]
            files = site_build.issue_files(g, {}, g["game_id"], rows)
            assert files, (gid, key)
            audio_script.build(g, None)
            if key == "quarters" and variant == "missing":
                page = next(b for p, (b, t) in files.items() if p.endswith("/index.html")).decode()
                assert "Quarter scores aren" in page
