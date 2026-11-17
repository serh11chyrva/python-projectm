# Installation

Install a binary wheel from PyPI:

```console
python -m pip install python-projectm
```

Version 1.0.0 provides Windows x64 wheels for standard CPython 3.11–3.14.
Each wheel contains projectM 4.1.6, the Python-facing native
wrapper, and the required redistributable native dependencies. Installation
does not invoke CMake or download projectM. PyPI contains no source distribution,
so unsupported systems receive pip's "no matching distribution" error instead
of an attempted native build.

Rendering needs a system desktop OpenGL 3.3+ implementation and a usable context.
GLFW and Qt normally need a graphical session. NumPy output still renders through
OpenGL. Graphics drivers are not bundled; a compatible software driver can be
used on machines without GPU acceleration.

## Optional integrations

```console
python -m pip install "python-projectm[glfw]"
python -m pip install "python-projectm[pyside6]"
python -m pip install "python-projectm[glfw,pyside6]"
```

GLFW is needed for `GLFWRenderer` and the default hidden-window `NumpyRenderer`.
Qt renderers use the `pyside6` extra and follow Qt's Windows system requirements.
Linux and macOS wheels are not part of the 1.0.0 release.

The ModernGL adapter borrows a context from the application's existing ModernGL
installation. It does not install ModernGL or create a second context. NumPy
output can borrow a GLFW, ModernGL, Qt, or custom adapter.

## Check native loading

This query does not create an OpenGL context:

```console
python -c "from python_projectm.core.version import get_version_string; print(get_version_string())"
```

The native version is `4.1.6`; it is separate from the Python distribution version
`1.0.0`. See the [quick start](quickstart.md) to render the packaged preset from
any directory. A repository checkout is not required for that example.

For development, custom native libraries, and editable installation, follow
[building from source](source-build.md). Corresponding sources are attached to
each [GitHub Release](https://github.com/serh11chyrva/python-projectm/releases).
