# Troubleshooting

## Native installation

The following build and loader notes are shared with the repository README.

```{include} ../README.md
:start-after: <!-- docs-troubleshooting-start -->
:end-before: <!-- docs-troubleshooting-end -->
```

## Missing native symbol

Rebuild projectM and `pypm_capi` together through the root CMake project using
the [installation guide](installation.md). The framebuffer adaptation and
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
