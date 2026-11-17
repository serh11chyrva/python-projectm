# Maintaining documentation

Documentation uses [Sphinx](https://www.sphinx-doc.org/), the
[Shibuya theme](https://shibuya.lepture.com/), and
[MyST Parser](https://myst-parser.readthedocs.io/) for Markdown pages.
The [API reference](api/index.rst) is generated from source docstrings with
Sphinx autodoc and Napoleon's Google-style docstring support.

## Build locally

Run from the repository root with Python 3.11 or newer supported by the pinned
documentation dependencies. With the `uv` installation described in the root
README, this command uses an isolated temporary environment:

```powershell
uv run --isolated --no-project --with-requirements docs/requirements.txt python -m sphinx -b html -W --keep-going docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser. The `_build` directory is
ignored by Git. `--no-project` keeps this command independent of the application's
environment and lockfile. It installs the documentation requirements without
syncing the project's runtime extras or building native libraries.

Alternatively, in an existing dedicated documentation environment:

```powershell
python -m pip install -r docs/requirements.txt
python -m sphinx -b html -W --keep-going docs docs/_build/html
```

For a full rebuild after changing configuration or docstrings, add `-E -a`.
To check external links separately, use Sphinx's link checker:

```powershell
uv run --isolated --no-project --with-requirements docs/requirements.txt python -m sphinx -b linkcheck docs docs/_build/linkcheck
```

Link checking needs network access and external sites can reject automated
requests. It is separate from the strict HTML build, which validates source
syntax, internal page references, and autodoc imports.

## Build dependencies and imports

`docs/requirements.txt` pins documentation tools independently of `uv.lock` and
the root runtime `requirements.txt`. NumPy is installed for real array types.
Autodoc mocks OpenGL, GLFW, PySide6, and shiboken6 so documentation builds need
neither a display server nor native projectM binaries. The actual project Python
modules and their docstrings are read from the checkout through `docs/conf.py`.
The configuration supplies a type placeholder for `QOpenGLContext` before
importing Qt adapters, because their evaluated union annotations require a type
rather than Sphinx's default mock instance.

Do not instantiate renderers or call version functions from Sphinx configuration
or module-level examples. Such calls would load native libraries or require an
OpenGL context. Source code examples are displayed without execution.

The project name, author, and release come from `pyproject.toml`; no second
documentation version string needs updating for a release.

## Edit pages and API docs

- Write documentation and docstrings in English.
- Add new pages to a `toctree` in `index.md` or the relevant reference index.
- Use Markdown for guides and reStructuredText directives for API pages.
- Keep the README focused on binary installation and a self-contained quick start.
- Maintain native toolchains and editable commands in `source-build.md`, and
  user-facing loader and context advice in `troubleshooting.md`.
- Add exported classes and functions to the appropriate `docs/api/` page.
- Describe arguments, return values, meaningful exceptions, ownership, and thread
  or context requirements in public API docstrings.
- Use Google-style `Args:`, `Returns:`, and `Raises:` sections where useful.
- Avoid importing optional toolkits outside their integration layer.

The initial docstring audit found missing documentation across core sizing,
presets, mesh parameters, version queries, renderer methods, adapters, and Qt
worker shutdown. Those definitions now have docstrings. Generated parameter
properties retain their existing runtime documentation. Qt event callbacks
and internal helpers are documented in source; the public API pages focus on
application entry points and avoid listing the whole inherited Qt/Thread API.
Generated ctypes entry points follow the C header described in the
[native reference](api/native.rst), rather than duplicating the ABI as Python
function docstrings.

## Configuration references

The build follows the official [Sphinx autodoc documentation](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html),
[Shibuya configuration](https://shibuya.lepture.com/customisation/), and
[Read the Docs configuration reference](https://docs.readthedocs.com/platform/stable/config-file/v2.html).
See [publishing](publishing.md) for repository import and version setup.
