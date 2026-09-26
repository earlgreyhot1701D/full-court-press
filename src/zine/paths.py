"""Where templates/ and static/ live, in the repo and in the Lambda bundle.

Repo:   <repo>/src/zine/paths.py  -> templates at <repo>/templates
Bundle: <bundle>/zine/paths.py    -> templates at <bundle>/templates   (tools/build_lambda.py)
"""
import os

PKG = os.path.dirname(os.path.abspath(__file__))


def root():
    for c in (os.path.dirname(os.path.dirname(PKG)), os.path.dirname(PKG)):
        if os.path.isdir(os.path.join(c, "templates")):
            return c
    raise RuntimeError("templates/ not found next to the zine package")


ROOT = root()
TEMPLATES = os.path.join(ROOT, "templates")
STATIC = os.path.join(ROOT, "static")


def rel_root(site_path):
    """Relative prefix from a page at `site_path` (site-root relative, '/'-separated) back to the root."""
    return "../" * site_path.count("/")
