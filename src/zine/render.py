"""render.py . Jinja2 -> HTML strings. One responsibility: turn a template name
plus a context dict into an HTML string. Autoescape is on; nothing model- or
feed-derived is ever marked safe. No I/O beyond loading templates from disk.
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape

from zine.paths import TEMPLATES

_TEMPLATES_DIR = TEMPLATES

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(enabled_extensions=("html",), default=True),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render(template_name, context):
    """Render a template to an HTML string. Autoescape on; no |safe anywhere."""
    return _env.get_template(template_name).render(**context)
