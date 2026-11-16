# Tests

The suite uses Python's standard `unittest` runner; no test dependency is needed.
Run commands from the repository root, using the existing environment described
in [README.md](../README.md). These commands never install or synchronize packages.

## Unit tests

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -t . -v
```

The default run covers PCM layouts, dtype dispatch, native block sizes, argument
validation, lazy ctypes symbols, and allocated string ownership. It does not
load a DLL or create a GL context. The three OpenGL test modules are skipped.

## Real rendering tests

Build projectM and `pypm_capi` together first, following the root README. Install
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

To select only one adapter:

```powershell
$env:PYTHON_PROJECTM_RUN_GL_TESTS = '1'
.venv/Scripts/python.exe -m unittest tests.integration.test_pyside6 -v
```

Use `tests.integration.test_glfw_numpy` or `tests.integration.test_moderngl` for
the other adapters. On Linux/macOS use the environment's Python executable and
the equivalent shell environment-variable syntax. Those platforms still need
matching native libraries and a supported OpenGL backend.
