# Tests

The suite uses Python's standard `unittest` runner; no test dependency is needed.
Run commands from the repository root, using the existing environment described
in the [source guide](../docs/source-build.md). These commands never install or synchronize packages.

## Unit tests

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -t . -v
```

The default run covers PCM layouts, dtype dispatch, native block sizes, argument
validation, lazy ctypes symbols, and allocated string ownership. It does not
load a DLL or create a GL context. It also checks the examples' synthetic PCM,
streaming WAV conversion/looping, and truncated-file handling. The three OpenGL
test modules are skipped.

## Real rendering tests

Prepare an editable native build or select a manual wrapper using
`PYTHON_PROJECTM_LIBRARY`, following the source guide. Install
the desired optional dependencies before running these tests: GLFW for GLFW and
default NumPy rendering, PySide6 for Qt, and the application's ModernGL package
for ModernGL. The tests do not install missing dependencies.

```powershell
$env:PYTHON_PROJECTM_RUN_GL_TESTS = '1'
.venv/Scripts/python.exe -m unittest discover -s tests -t . -v
Remove-Item Env:PYTHON_PROJECTM_RUN_GL_TESTS
```

The opt-in run loads the actual native libraries and creates desktop OpenGL 3.3+
contexts. It requires a graphics driver and a desktop session. GLFW windows are
hidden; the Qt widget tests briefly show small windows. Missing optional Python
packages cause skips. Once a package is present, context creation or rendering
failures fail the test instead of being reported as skips.

The tests use an original constant-color preset held in memory, so no downloaded
presets, textures, audio devices, or network access are needed. Pixel assertions
check the rendered color, including nonzero framebuffer targets. Coverage includes
core parameters and all PCM formats, GL state and thread/context ownership,
preset failure recovery, NumPy output reuse and orientation, ModernGL external
resource ownership, Qt queued PCM, widget resize/cleanup, offscreen rendering,
and background rendering with GUI-thread frame delivery and orderly shutdown.
The PySide6 studio is exercised in both modes, including controls, PNG snapshots,
and recovery from invalid preset input.

To select only one adapter:

```powershell
$env:PYTHON_PROJECTM_RUN_GL_TESTS = '1'
.venv/Scripts/python.exe -m unittest tests.integration.test_pyside6 -v
```

Use `tests.integration.test_glfw_numpy` or `tests.integration.test_moderngl` for
the other adapters. Custom Linux/macOS builds need matching native libraries,
a supported OpenGL backend, and equivalent shell environment-variable syntax.
They are outside the supported 1.0.0 release and CI matrix.

## GitHub Actions

CI runs the existing unit suites on Windows x64 and CPython 3.11–3.14.
Separate jobs build the Windows wheel and copy `tests/` and `examples/` outside
the checkout before running `tools/run_ci_tests.py --integration`. This ensures
the rendering tests import the installed wheel and use its native resources.
All optional integration packages are installed for this run; unexpected skips
fail the required job. Mesa supplies software OpenGL on Windows.
No test cases are added or rewritten by this packaging workflow.
