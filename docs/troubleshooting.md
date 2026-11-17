# Troubleshooting

## Native installation

- **No matching distribution:** use standard CPython 3.11–3.14, Windows x64 or
  Linux x86_64 with glibc 2.28+. macOS, ARM, musl, and free-threaded Python are
  outside the supported binary matrix. See [source builds](source-build.md)
  for custom builds; PyPI does not provide a compilation fallback.
- **Missing wrapper or DLL load failure:** reinstall the matching wheel in the
  active Python environment. Native libraries must have the same architecture
  as Python. Official wheels include projectM, GLEW where needed, and app-local
  MSVC runtime files; a separate projectM or VC++ redist installation is not
  part of the normal wheel procedure.
- **Unexpected library selected:** check `PYTHON_PROJECTM_LIBRARY`. This optional
  override selects a custom wrapper and its sibling dependencies before the
  first native call. Unset it to use the packaged libraries.
- **Source build fails to find GLEW:** use the Windows vcpkg toolchain in the
  [source guide](source-build.md), with the shared `x64-windows` triplet.
- **Qt platform plugin fails on Linux:** the PySide6 extra needs glibc 2.34+
  and the system libraries required by its XCB platform plugin, including
  `libxcb-cursor0` on Ubuntu. A working graphics driver and session are still needed.

## Missing native symbol

For a wheel, reinstall the current matching distribution. For a custom build,
rebuild projectM and `pypm_capi` together through the root CMake project using
the [source guide](source-build.md). The framebuffer adaptation and
wrapper must be deployed together; an older wrapper or unrelated projectM
binary does not provide the expected behavior.

## Wrong context or thread

{py:class}`~python_projectm.ProjectMContextError` means the creating thread or
original OpenGL context is unavailable. Shared contexts cannot substitute for
the original context. Use `with renderer.current() as pm:` for direct core
calls through a managed renderer and close resources before their context.

GLFW window operations and event polling belong on the main thread. Qt widgets
belong on the GUI thread. Use `RenderThread`'s queued methods when rendering on
a Qt worker; never call the worker's core from an audio callback.

## Unsupported PCM

Automatic `add_pcm` dispatch accepts floating-point, signed int16, and uint8
arrays. A Python list of integers usually becomes int64, which is rejected.
Choose an explicit dtype or use a typed submission method with correctly scaled
input. Mono/stereo arrays use `(frames, 1)` or `(frames, 2)`, not planar
`(2, frames)` storage. See [PCM audio](integrations.md#pcm-audio).

## NumPy output still requires OpenGL

The NumPy renderer reads pixels back from a GL framebuffer. A hidden window
does not remove the graphics-driver requirement. A machine without a GPU needs
a compatible software desktop OpenGL implementation. EGL applications must set
`PYOPENGL_PLATFORM=egl` before importing `OpenGL` or `python_projectm`.

## Documentation warnings

Use the strict build command in [maintaining documentation](documentation.md).
Unresolved page links, invalid directives, and autodoc import warnings fail the
build. Documentation needs no native binaries or GUI application: GUI and
OpenGL imports are mocked by `docs/conf.py`, while NumPy is installed normally.
