from pathlib import Path
import importlib.metadata
import re

from hyperlink import URL
from sphinx.ext.intersphinx import resolve_reference_in_inventory

DOCS = Path(__file__).parent

GITHUB = URL.from_text("https://github.com/")
HOMEPAGE = GITHUB.child("python-jsonschema", "referencing")

project = "referencing"
author = "Julian Berman"
copyright = "2022, " + author

release = importlib.metadata.version("referencing")
version = release.partition("-")[0]

language = "en"
default_role = "any"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx_click",
    "sphinx_copybutton",
    "sphinx_json_schema_spec",
    "sphinxcontrib.spelling",
]

pygments_style = "lovelace"
pygments_dark_style = "one-dark"

html_theme = "furo"
html_static_path = []

# See sphinx-doc/sphinx#10785
_TYPE_ALIASES = {
    "Schema",
}


def _resolve_broken_refs(app, env, node, contnode):
    if node["refdomain"] != "py":
        return

    # Evade tobgu/pyrsistent#267
    if node["reftarget"].startswith("pyrsistent.typing."):
        node["reftarget"] = node["reftarget"].replace(".typing.", ".")
        return resolve_reference_in_inventory(
            env, "pyrsistent", node, contnode
        )
    elif node["reftarget"] == "PList":
        node["reftarget"] = "pyrsistent.PList"
        return resolve_reference_in_inventory(
            env, "pyrsistent", node, contnode
        )
    elif node["reftarget"] in _TYPE_ALIASES:
        return app.env.get_domain("py").resolve_xref(
            env,
            node["refdoc"],
            app.builder,
            "data",
            node["reftarget"],
            node,
            contnode,
        )


def setup(app):
    app.connect("missing-reference", _resolve_broken_refs)


# -- Extension configuration -------------------------------------------------

# -- Options for autodoc extension -------------------------------------------

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
}

# -- Options for autosectionlabel extension ----------------------------------

autosectionlabel_prefix_document = True

# -- Options for intersphinx extension ---------------------------------------

intersphinx_mapping = {
    "pyrsistent": ("https://pyrsistent.readthedocs.io/en/latest/", None),
    "python": ("https://docs.python.org/", None),
}

# -- Options for extlinks extension ------------------------------------------

extlinks = {
    "gh": (str(HOMEPAGE.child("%s")), None),
    "github": (str(GITHUB.child("%s")), None),
}

# -- Options for the linkcheck builder ---------------------------------------


def entire_domain(host):
    return r"http.?://" + re.escape(host) + r"($|/.*)"


linkcheck_ignore = [
    entire_domain("codecov.io"),
    entire_domain("img.shields.io"),
    f"{GITHUB}.*#.*",
    str(HOMEPAGE.child("actions")),
    str(HOMEPAGE.child("python-jsonschema/workflows/CI/badge.svg")),
]

# -- Options for spelling extension ------------------------------------------

spelling_show_suggestions = True
