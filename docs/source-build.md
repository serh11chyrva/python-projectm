# Building from source

Binary PyPI installation is described in [installation](installation.md).
Source builds are for development and modified native libraries. They require
a C++ compiler, system OpenGL development files, and network access to build
tools and any native sources not already present.

The build backend is scikit-build-core. Building a wheel or running `uv sync`
now invokes CMake and builds both projectM and the wrapper. Runtime Python
dependencies remain recorded in `uv.lock`; build tools are pinned separately
in `pyproject.toml`.

## Get sources

Clone the repository, or extract `python_projectm-<version>.tar.gz` from the
matching [GitHub Release](https://github.com/serh11chyrva/python-projectm/releases).
No submodule initialization is required.

A release source archive already includes projectM 4.1.6 and its vendors, GLEW
2.2.0, build scripts, licenses, and `native-sources.json`. In a fresh Git checkout,
CMake downloads the official projectM release archive into its build tree and
verifies the recorded SHA-256. To prepare both upstream trees explicitly before
creating a source archive, use:

```console
python tools/prepare_sources.py
```

This command refuses to replace existing upstream directories. Skip it when
sources are already present. `PYPM_PROJECTM_SOURCE_DIR` can select an existing
extracted projectM 4.1.6 tree through a CMake definition. The build expects the
release archive with bundled dependencies, not GitHub's automatic source ZIP.

## Windows x64

Use 64-bit Python 3.11–3.14, Git, and Visual Studio 2022 or Build Tools 2022 with
**Desktop development with C++**, MSVC v143, and a Windows SDK. Python and all
native libraries must use the same architecture.

The following PowerShell commands prepare the pinned vcpkg checkout in a new
ignored build directory. Run them from the repository or release-source root:

```powershell
git clone https://github.com/microsoft/vcpkg.git build/vcpkg
if ($LASTEXITCODE -ne 0) { throw 'vcpkg clone failed.' }
git -C build/vcpkg checkout ef7dbf94b9198bc58f45951adcf1f041fcbc5ea0
if ($LASTEXITCODE -ne 0) { throw 'vcpkg checkout failed.' }
& ./build/vcpkg/bootstrap-vcpkg.bat -disableMetrics
if ($LASTEXITCODE -ne 0) { throw 'vcpkg bootstrap failed.' }
$env:CMAKE_TOOLCHAIN_FILE = (Resolve-Path './build/vcpkg/scripts/buildsystems/vcpkg.cmake').Path
```

With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```powershell
uv sync --locked --extra glfw
```

The vcpkg manifest selects GLEW 2.2.0 at the pinned baseline. CMake builds shared
projectM and `pypm_capi`, installs them and GLEW into the package, and includes
the Release MSVC runtime for app-local deployment. It does not require a
system-wide projectM installation. Use `--extra pyside6` or `--all-extras` as needed.

## Linux x86_64

For an Ubuntu development machine, install a C++ compiler and OpenGL headers:

```console
sudo apt-get install build-essential libgl1-mesa-dev libx11-dev libxext-dev
uv sync --locked --extra glfw
```

The local wheel targets the build machine. Portable release wheels are built
by CI in the pinned manylinux_2_28 image and repaired with auditwheel. Do not
retag a wheel built on a newer system to claim older glibc compatibility.

## Editable development and native changes

`uv sync` installs editable Python sources and installed native resources.
It reuses a compatible existing `.venv`; `--inexact` retains unrelated installed
packages. After changing C++ code or CMake settings, explicitly rebuild:

```console
uv sync --locked --reinstall-package python-projectm --extra glfw
```

After editing runtime dependency declarations, update `uv.lock` and regenerate
the root `requirements.txt` as described in
[contributing](https://github.com/serh11chyrva/python-projectm/blob/main/CONTRIBUTING.md).
Documentation dependencies remain separate.

For C++ iteration, the manual root CMake build remains available. For example,
with the Windows toolchain variable set above:

```powershell
cmake -S . -B build/native -G "Visual Studio 17 2022" -A x64 `
    "-DCMAKE_TOOLCHAIN_FILE=$env:CMAKE_TOOLCHAIN_FILE" `
    -DVCPKG_TARGET_TRIPLET=x64-windows
if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed.' }
cmake --build build/native --config Release --target pypm_capi --parallel
if ($LASTEXITCODE -ne 0) { throw 'Native build failed.' }
```

Manual builds copy runtime libraries to `python_projectm/native/bin/` by default.
Set `PYPM_COPY_NATIVE_TO_SOURCE=OFF` to disable this. PEP 517 builds disable it
and use CMake's `python` install component, so old local DLLs cannot enter a wheel.
To select a manual build explicitly, set `PYTHON_PROJECTM_LIBRARY` to its wrapper's
absolute path before the first native call. Windows sibling DLLs are discovered
from that directory; Linux builds use relative library paths.

Build through the root project. Its generated `ProjectM.cpp` adaptation preserves
the caller's draw framebuffer. An unrelated prebuilt projectM 4.1.6 library does
not provide this behavior. Upstream source files and the public C ABI are retained.

## Build a local wheel

```console
uv build --wheel
```

The backend builds native libraries automatically. Windows produces a
`py3-none-win_amd64` wheel. A local Linux wheel requires manylinux construction
and repair before public distribution. The [release workflow](publishing.md)
does this and tests the resulting wheel on every supported Python version.

Tests and documentation builds are separate actions; see
[tests](https://github.com/serh11chyrva/python-projectm/blob/main/tests/README.md)
and [maintaining documentation](documentation.md).
