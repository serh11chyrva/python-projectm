# python-projectm

Python bindings for the projectM music visualizer, with a shared rendering core
and adapters for GLFW, ModernGL, PySide6, and NumPy.

Use an existing desktop OpenGL context, embed a visualizer in a Qt application,
render into a ModernGL texture, or read RGBA frames into a NumPy array. The
bindings accept PCM for visualization; they do not capture or play audio.

```{important}
Rendering requires desktop OpenGL 3.3 or newer and matching projectM and wrapper
libraries built through this repository's root CMake project. NumPy output still
uses OpenGL. The documented native build procedure targets Windows x64.
```

Start with the [installation guide](installation.md), then follow the
[quick start](quickstart.md). The [integration guide](integrations.md) explains
context ownership and includes complete adapter examples.

| Application needs | Entry point |
| --- | --- |
| An existing OpenGL context and framebuffer | {py:class}`python_projectm.ProjectM` |
| A GLFW visualization window | {py:class}`python_projectm.integrations.glfw.GLFWRenderer` |
| A texture for ModernGL composition | {py:class}`python_projectm.integrations.moderngl.ModernGLRenderer` |
| A Qt GPU widget | {py:class}`python_projectm.integrations.pyside6.ProjectMWidget` |
| RGBA arrays in CPU memory | {py:class}`python_projectm.integrations.numpy.NumpyRenderer` |

```{toctree}
:maxdepth: 2
:caption: User guide

installation
quickstart
integrations
examples
troubleshooting
```

```{toctree}
:maxdepth: 2
:caption: Reference

api/index
architecture
licensing
```

```{toctree}
:maxdepth: 1
:caption: Contributing

documentation
publishing
```
