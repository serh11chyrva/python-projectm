# Publishing on Read the Docs

The repository includes `.readthedocs.yaml`, using configuration version 2,
Ubuntu 24.04, Python 3.12, and `docs/conf.py`. The build installs only
`docs/requirements.txt` and produces HTML with the Shibuya theme. Sphinx warnings
fail the Read the Docs build.

No projectM source download, CMake build, graphics driver, display server, or
native library upload is required for documentation. Autodoc reads the real
Python source with optional GUI and OpenGL packages mocked.

## Connect the repository

1. Push the documentation commits to the GitHub repository when ready.
2. Sign in to [Read the Docs](https://app.readthedocs.org/) and add the
   `serh11chyrva/python-projectm` repository through its
   [project import flow](https://docs.readthedocs.com/platform/stable/intro/add-project.html).
   Install the Read the Docs GitHub App with access to this repository when
   using the GitHub App integration.
3. Select the repository's `main` branch as the default documentation version.
   Keep the configuration file path at the root `.readthedocs.yaml`.
4. Trigger the first build and inspect its log. It should use `docs/conf.py`,
   install the pinned requirements, and build the HTML pages without native
   compilation.
5. Verify that the GitHub webhook/integration is connected so future pushes
   rebuild the documentation. Enable pull request previews in project settings
   if desired.
6. Open the resulting site and check navigation, API signatures, source links,
   search, and light/dark appearance. Add its actual URL to repository metadata
   and the README after the project slug is assigned.

The configuration prepares the repository; it does not create a Read the Docs
project or enable GitHub webhooks automatically. The public site address depends
on the project slug assigned during import.

## Versions and releases

`latest` tracks the configured default branch. Activate release tags in the
Read the Docs project's version settings to publish matching documentation
versions. Select a stable default version after the corresponding release is
ready. Each version builds from its own committed configuration and docstrings.

Sphinx reads the Python distribution release from `pyproject.toml`. Native
projectM version queries remain separate and are never executed during the
documentation build. Read the Docs supplies the canonical URL used by
`html_baseurl`; local builds leave it unset.
The theme's source links use the selected branch or tag; pull request builds
link to the checked-out commit.

## Updating the documentation stack

Update documentation pins in `docs/requirements.txt`, run the strict
[local HTML build](documentation.md#build-locally), and review the generated
site before committing. Documentation dependencies are maintained separately
from application dependencies, so these updates do not require regenerating
the runtime lockfile or root `requirements.txt`.

For platform details, see the official
[Read the Docs Sphinx guide](https://docs.readthedocs.com/platform/stable/intro/sphinx.html)
and [configuration reference](https://docs.readthedocs.com/platform/stable/config-file/v2.html).
