"""Sphinx configuration for local and Read the Docs builds."""

import os
import sys
import tomllib
from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Read metadata without importing projectM or loading the native wrapper.
metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
project = metadata["name"]
author = ", ".join(person["name"] for person in metadata["authors"])
copyright = f"2026, {author}"
release = metadata["version"]
version = ".".join(release.split(".")[:2])
language = "en"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Imports expose the actual Python API without a display server, native binaries,
# or optional GUI packages. NumPy stays real for array annotations and signatures.
autodoc_mock_imports = ["OpenGL", "glfw", "PySide6", "shiboken6"]
autodoc_member_order = "bysource"
autodoc_typehints = "signature"
autodoc_typehints_format = "short"
add_module_names = False
napoleon_google_docstring = True
napoleon_numpy_docstring = False
myst_heading_anchors = 3

html_theme = "shibuya"
html_title = f"{project} {release}"
html_theme_options = {
    "accent_color": "violet",
    "github_url": metadata["urls"]["Repository"],
}
source_ref = os.environ.get("READTHEDOCS_GIT_IDENTIFIER", "main")
if os.environ.get("READTHEDOCS_VERSION_TYPE") == "external":
    source_ref = os.environ.get("READTHEDOCS_GIT_COMMIT_HASH", "main")
html_context = {
    "source_type": "github",
    "source_user": "serh11chyrva",
    "source_repo": "python-projectm",
    "source_version": source_ref,
    "source_docs_path": "/docs/",
}

# Read the Docs supplies this URL for each version, including preview builds.
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")
if os.environ.get("READTHEDOCS") == "True":
    html_context["READTHEDOCS"] = True


def _prepare_qt_autodoc(app):
    """Keep evaluated Qt union annotations importable without installing Qt."""
    from sphinx.ext.autodoc.mock import mock

    with mock(app.config.autodoc_mock_imports):
        qt_gui = import_module("PySide6.QtGui")
        # A real type supports QOpenGLContext | None; Sphinx's mock instance does not.
        qt_gui.QOpenGLContext = type(
            "QOpenGLContext", (), {"__module__": "PySide6.QtGui"}
        )
        import_module("python_projectm.integrations.pyside6")


def _project_source_module(app, module_name, fullname):
    """Keep source links with the owning class, including inherited and Qt members."""
    if module_name and (module_name == "python_projectm" or module_name.startswith("python_projectm.")):
        owner = getattr(import_module(module_name), fullname.split(".")[0], None)
        return getattr(owner, "__module__", None)
    return None


def setup(app):
    """Prepare API imports and source links before reading reference pages."""
    app.connect("builder-inited", _prepare_qt_autodoc)
    app.connect("viewcode-follow-imported", _project_source_module)
