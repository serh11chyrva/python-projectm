# Publishing packages and documentation

## PyPI setup

Version 1.0.0 publishes one Windows x64 wheel for CPython 3.11–3.14.
Linux and macOS wheels are outside this release. The corresponding source
archive is a GitHub Release asset and is deliberately excluded from the PyPI
upload, preventing pip from attempting native compilation on unsupported systems.

Before the first release, configure [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/):

1. Sign in to the PyPI account that will own `python-projectm` and enable the
   account's required two-factor authentication.
2. If the project does not exist, create a pending publisher for project name
   `python-projectm`. If it already exists, add a publisher in that project's
   publishing settings; verify that the release version is still available.
3. Use GitHub owner `serh11chyrva`, repository `python-projectm`, workflow filename
   `release.yml`, and environment name `pypi`.
4. Create the GitHub repository environment `pypi`. Under **Deployment branches
   and tags**, select **Selected branches and tags** and add two rules: a
   **Branch** rule for `main`, and a **Tag** rule for `v*`. Both are needed for
   manual and GitHub Release publication respectively. If the environment
   previously allowed only `v*` tags, add the `main` branch rule before a manual run.
   Required reviewers are not part of the automatic publishing setup.

No long-lived PyPI API token is used. Only the publishing job receives
`id-token: write`; the asset-upload job separately receives `contents: write`.
PR and ordinary CI jobs have read-only repository permissions. Creating the
workflow files does not configure either service account automatically.

## Manual publication from main

1. Keep `pyproject.toml` at the intended version (`1.0.0` for the first release),
   update the changelog with the release date, and merge the release changes.
2. Open the repository's **Actions** tab, select **Publish release**, click
   **Run workflow**, select branch **main**, and confirm **Run workflow**.
   `workflow_dispatch` starts a publishing run, not an immediate upload.
3. The workflow captures that commit and reads the stable version from its
   metadata. If `v1.0.0` already exists, it must point to the same commit.
   Existing release tags are never moved or overwritten.
4. The workflow calls the shared CI and requires every job to pass: Windows
   unit tests on Python 3.11–3.14, strict Sphinx HTML, corresponding sources,
   the Windows wheel, and installed OpenGL tests on all four Python versions.
   Documentation and source-archive jobs use Ubuntu without Linux native builds.
5. After CI succeeds, it creates the matching stable GitHub Release and tag if
   absent, using the exact tested commit. An existing release must be published
   and stable. It attaches the verified Windows wheel,
   `python_projectm-<version>.tar.gz`, and `SHA256SUMS`. This makes corresponding
   sources available before PyPI publication.
6. The publishing job downloads those same wheel artifacts and uploads them
   through the PyPA publish action with OIDC and its provenance attestations.
   It does not rebuild, retag, or upload the source archive.
7. Inspect the PyPI description and documentation link, confirm the
   `py3-none-win_amd64.whl` file is present, and activate the matching Read the Docs
   version as needed.

The manual publishing run must use `main`. Do not run `release.yml` until the
PyPI publisher and GitHub `pypi` environment are configured: a successful run
publishes the package automatically after CI.

## Publication from a GitHub Release

Alternatively, tag the intended commit `v1.0.0` and publish a stable GitHub
Release. That event starts the same CI, asset-upload, and PyPI publishing jobs.
The tag must exactly match the stable project version. Published prereleases
do not trigger production publication. A Release created by the manual workflow
using `GITHUB_TOKEN` does not start a second publishing run.

Pushes, pull requests, and manual runs of `ci.yml` build artifacts without
publishing them. Only `release.yml` publishes, through its manual trigger or a
stable GitHub Release. Publishing runs are serialized to avoid overlapping uploads.
Package versions and filenames on PyPI cannot be overwritten: if a release upload fails,
inspect whether any files were accepted before retrying or choosing a new version.
No automatic `skip-existing` policy hides conflicting uploads.

An upload rejected with HTTP 400 requires reading the publishing job's verbose
response before retrying. CI checks wheel classifiers against the pinned
`trove-classifiers` catalog as well as running `twine check --strict`;
description validation alone does not check classifier membership.
Re-running a failed publishing job reuses its original wheel. Changes to
package metadata require a fresh build and CI run. If the release tag already
points to the previous commit, choose a new version or explicitly authorize a
tag correction; the workflow never moves an existing tag automatically.

## Artifact contents and reproducibility

`native-sources.json` pins the official projectM and GLEW release archives and
their checksums. Source preparation rejects mismatches and existing destination
trees. The source archive contains the full projectM vendor sources, the GLEW
release sources, wrapper, framebuffer adaptation, license notices, and build
scripts. Windows GLEW build patches are identified by the pinned vcpkg commit.

The native build disables unused playlist/UI components and upstream tests,
uses the distributed parser sources, and leaves upstream source files unchanged.
Only the CMake `python` install component enters a wheel. Native SDK headers,
import libraries, debug files, and local checkout binaries are excluded.

Wheels use `py3-none` platform tags because ctypes does not depend on a Python
extension ABI. Windows repair uses `--analyze-existing` to inspect packaged DLLs
and `--ignore-existing` to resolve dependencies from inside the extracted wheel.
It preserves DLL filenames and checks that every non-system PE dependency is
bundled. Release artifact checks require the `win_amd64` platform tag and reject
non-Windows native binaries.
The installed suite checks loading and rendering without build-machine paths;
CI fails if an expected integration is skipped.

Each wheel contains `python_projectm/native/native-build.txt` with compiler,
flags, source checksum, and framebuffer adaptation details. Actions are pinned
to commits and native inputs to checksums/baselines.
These controls identify build inputs; they do not promise bit-for-bit identical
native binaries across hosted compiler image updates. See [licensing](licensing.md)
and [source builds](source-build.md) for replacement and rebuild instructions.

## Read the Docs setup

The repository includes `.readthedocs.yaml`, using configuration version 2,
Ubuntu 24.04, Python 3.12, and `docs/conf.py`. The build installs only
`docs/requirements.txt` and produces HTML with the Shibuya theme. Sphinx warnings
fail the Read the Docs build.

No projectM source download, CMake build, graphics driver, display server, or
native library upload is required for documentation. Autodoc reads the real
Python source with optional GUI and OpenGL packages mocked.

### Connect the repository

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
6. Verify the project slug is `python-projectm` and the public URL is
   https://python-projectm.readthedocs.io/en/latest/. That URL is already included
   in package metadata and the README. Check navigation, API signatures, source
   links, search, and light/dark appearance after the first successful build.

The configuration prepares the repository; it does not create a Read the Docs
project or enable GitHub webhooks automatically. The public site address depends
on the project slug assigned during import.

### Versions and releases

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

### Updating the documentation stack

Update documentation pins in `docs/requirements.txt`, run the strict
[local HTML build](documentation.md#build-locally), and review the generated
site before committing. Documentation dependencies are maintained separately
from application dependencies, so these updates do not require regenerating
the runtime lockfile or root `requirements.txt`.

For platform details, see the official
[Read the Docs Sphinx guide](https://docs.readthedocs.com/platform/stable/intro/sphinx.html)
and [configuration reference](https://docs.readthedocs.com/platform/stable/config-file/v2.html).
