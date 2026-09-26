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
            if u.startswith(("http", "mailto", "data:")) or not re.search(r"\.(html|css|js|png|mp3|ttf|json)$", u):
                continue
            n += 1
            if not os.path.exists(os.path.normpath(os.path.join(here, u))):
                bad.append((path, u))
    assert n > 300 and not bad, bad[:5]
