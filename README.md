# python-projectm

Python bindings for the projectM OpenGL music visualizer, with an optional PySide6 integration.

## Licensing

`python-projectm` provides Python bindings for [projectM](https://github.com/projectM-visualizer/projectm).
It is a binding project, not a fork of projectM.

- The original code in this repository, including the Python bindings in `python_projectm/`
  and the native C++ wrapper in `pypm_wrapper/`, is licensed under the **MIT License**.
  See [LICENSE](LICENSE) for the full terms.
- The **projectM library** is licensed separately under the **GNU Lesser General Public
  License v2.1 (LGPL v2.1)**. See the
  [upstream projectM license](https://github.com/projectM-visualizer/projectm/blob/v4.1.6/LICENSE.txt).
  This repository's MIT License does not relicense projectM.
- Other third-party dependencies retain their respective licenses.

If you redistribute projectM binaries, including DLLs bundled in a Python wheel, you must
also comply with the LGPL v2.1 terms, including the required copyright and license notices,
a copy of the license, and the applicable requirements for providing corresponding source
code and allowing users to use a modified version of the library. Refer to the upstream
license for the full requirements.

## Building from source on Windows (x64)

The instructions below use Visual Studio 2022, the Release configuration and 64-bit Python.
The native wrapper currently includes Windows-specific code; Linux and macOS builds are not covered here.
Run the PowerShell commands from the repository root unless noted otherwise.

### Prerequisites

- Git.
- Python 3.11–3.14, 64-bit.
- [uv](https://docs.astral.sh/uv/getting-started/installation/), available on `PATH`.
- Visual Studio 2022 or Build Tools 2022 with **Desktop development with C++**, MSVC v143 and a Windows SDK.
- CMake **3.21 or newer**, available on `PATH`.
- [vcpkg](https://learn.microsoft.com/en-us/vcpkg/get_started/get-started) installed and bootstrapped.
- An OpenGL-capable graphics driver for rendering.

Python, projectM, GLEW and the wrapper must all use the same architecture.

### 1. Get the repository

```powershell
git clone https://github.com/serh11chyrva/python-projectm.git
cd python-projectm
```

For an existing checkout, use its root directory instead.
No Git submodule initialization is required.

### 2. Download and extract projectM 4.1.6

Use the **libprojectM-4.1.6.tar.gz** asset attached to the
[projectM v4.1.6 release](https://github.com/projectM-visualizer/projectm/releases/tag/v4.1.6).
This is a source archive, so projectM must still be compiled.
Use this release asset rather than GitHub's automatically generated `Source code` archives:
the release archive includes the bundled dependencies needed for this build.

Download, check the release asset's SHA-256 and extract it:

```powershell
$archive = Join-Path $env:TEMP 'libprojectM-4.1.6.tar.gz'
Invoke-WebRequest `
    -Uri 'https://github.com/projectM-visualizer/projectm/releases/download/v4.1.6/libprojectM-4.1.6.tar.gz' `
    -OutFile $archive
$expectedSha256 = '1b9e6d56c59fe24e5416da4d42e941a34c982811003e43ac88b5aca8afa52c87'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expectedSha256) {
    throw 'projectM archive SHA-256 mismatch; do not extract it.'
}
if (Test-Path -LiteralPath './libprojectM-4.1.6') {
    throw 'libprojectM-4.1.6 already exists. Use it, or move it aside before extracting.'
}
tar -xzf $archive
if ($LASTEXITCODE -ne 0) { throw 'projectM extraction failed.' }
```

If the archive has already been downloaded and extracted, skip this step.
The source tree must look like this (avoid an extra nested directory):

```text
python-projectm/
├── CMakeLists.txt
├── pyproject.toml
├── libprojectM-4.1.6/
│   ├── CMakeLists.txt
│   ├── src/
│   └── vendor/
├── pypm_wrapper/
│   └── CMakeLists.txt
└── python_projectm/
    └── native/
        └── bin/
```

`libprojectM-4.1.6/` and compiled binaries are excluded from Git.
A fresh checkout needs this download step again.

### 3. Install GLEW with vcpkg

Set the path to your existing vcpkg installation, then install the shared x64 Windows package:

```powershell
$env:VCPKG_ROOT = 'C:\dev\vcpkg' # Replace with your vcpkg installation directory.
& "$env:VCPKG_ROOT/vcpkg.exe" install glew:x64-windows
if ($LASTEXITCODE -ne 0) { throw 'GLEW installation failed.' }
```

The CMake command below uses vcpkg in classic mode to find this package.
GLM and projectM-eval are built from the release archive's bundled sources;
SDL, playlist support and upstream tests are disabled for this wrapper build.
See [vcpkg's CMake integration documentation](https://learn.microsoft.com/en-us/vcpkg/users/buildsystems/cmake-integration)
for the toolchain and classic-mode settings.

### 4. Build projectM and the wrapper

Configure and build both native libraries through the root `CMakeLists.txt`:

```powershell
cmake -S . -B build/native -G "Visual Studio 17 2022" -A x64 `
    "-DCMAKE_TOOLCHAIN_FILE=$env:VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake" `
    -DVCPKG_MANIFEST_MODE=OFF `
    -DVCPKG_TARGET_TRIPLET=x64-windows `
    -DBUILD_SHARED_LIBS=ON `
    -DENABLE_SYSTEM_GLM=OFF `
    -DENABLE_SYSTEM_PROJECTM_EVAL=OFF `
    -DENABLE_PLAYLIST=OFF `
    -DENABLE_SDL_UI=OFF `
    -DBUILD_TESTING=OFF
if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed.' }

cmake --build build/native --config Release --target pypm_capi --parallel
if ($LASTEXITCODE -ne 0) { throw 'Native build failed.' }
```

There is no separate projectM build or system-wide installation step.
Linking through CMake targets builds projectM before the wrapper and uses the generated headers
from this build directory. After a successful build, CMake copies these runtime libraries into
`python_projectm/native/bin/`:

- `pypm_capi.dll` — the Python-facing C wrapper.
- `projectM-4.dll` — projectM.
- `glew32.dll` — GLEW, copied as a runtime dependency.

Use a fresh build directory when changing the generator, architecture or vcpkg toolchain.
The old `libprojectM-4.1.6/build/` directory is not used by these commands.

### 5. Install the Python package

Use the committed `uv.lock` to install the package in editable mode and its Python dependencies:

```powershell
uv sync --locked
```

For the optional PySide6 integration, use:

```powershell
uv sync --locked --extra pyside6
```

Use `--extra glfw` for GLFW, or `--all-extras` for both optional dependencies.

uv reuses an existing compatible `.venv` in the repository root, including one created by Poetry;
there is no need to delete it or run `uv venv`. If `.venv` does not exist, `uv sync` creates it.
To keep both optional integrations and any additional installed packages when adopting uv, use:

```powershell
uv sync --locked --all-extras --inexact
```

By default, `uv sync` removes packages that are not selected for installation;
`--inexact` retains them. See [uv's syncing documentation](https://docs.astral.sh/uv/concepts/projects/sync/).

`uv sync` installs the Python package and its Python dependencies; it does **not** run CMake.
Build the native libraries first. Rebuild them after changing the C++ sources.

Manage dependencies with `uv add <package>` and `uv remove <package>`.
After editing dependency declarations manually, run `uv lock` to update the lockfile.
Commit `pyproject.toml` and `uv.lock` together when dependencies change.

The committed `requirements.txt` contains pinned Python dependencies, including both optional
integrations, but excludes the local package itself. Regenerate it from the updated lockfile with:

```powershell
uv export --frozen --all-extras --no-emit-project --format requirements.txt --output-file requirements.txt
```

Include the regenerated `requirements.txt` in commits that update dependencies.

### 6. Verify the native library can load

```powershell
uv run --locked python -c "from python_projectm.core.version import get_version_string; print(get_version_string())"
```

The output should identify projectM 4.1.6. This checks DLL loading and the version API;
rendering additionally requires an active OpenGL context and a preset.

### Optional: build a wheel

After building the native libraries, create a wheel containing the DLLs:

```powershell
uv build --wheel
```

Wheels are written to `dist/`. This manual process bundles Windows x64 DLLs;
the current setuptools configuration does not automatically assign a Windows platform tag.
Do not publish its default `py3-none-any` wheel as a cross-platform package. Platform-specific
wheel tagging and CI packaging remain separate work.

## Troubleshooting

- **Missing `libprojectM-4.1.6/CMakeLists.txt`:** extract the release archive into the repository root.
- **GLEW not found during configuration:** check `VCPKG_ROOT`, install `glew:x64-windows`,
  and configure a fresh build directory using the toolchain above.
- **Missing `pypm_capi.dll`:** build the `pypm_capi` target and check `python_projectm/native/bin/`.
- **DLL loading fails:** check that all three runtime DLLs are present, all binaries and Python are x64,
  and the [Microsoft Visual C++ x64 Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
  is installed on the runtime machine.
