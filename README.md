# python-projectm

[![CI](https://github.com/serh11chyrva/python-projectm/actions/workflows/ci.yml/badge.svg)](https://github.com/serh11chyrva/python-projectm/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/python-projectm.svg)](https://pypi.org/project/python-projectm/)
[![Documentation](https://readthedocs.org/projects/python-projectm/badge/?version=latest)](https://python-projectm.readthedocs.io/en/latest/)

Python bindings for the [projectM](https://github.com/projectM-visualizer/projectm)
music visualizer. Turn PCM audio into MilkDrop-style visuals in an existing
OpenGL application, a GLFW window, a Qt widget, a ModernGL texture, or a NumPy
RGBA array.

**[Documentation](https://python-projectm.readthedocs.io/en/latest/)** ·
[Quick start](https://python-projectm.readthedocs.io/en/latest/quickstart.html) ·
[API reference](https://python-projectm.readthedocs.io/en/latest/api/index.html) ·
[Examples](https://github.com/serh11chyrva/python-projectm/tree/main/examples)

## Installation

```console
python -m pip install python-projectm
```

PyPI wheels include **projectM 4.1.6, the native wrapper, and their redistributable
runtime dependencies**. You do not need CMake, a compiler, vcpkg, or a separate
projectM installation. Python dependencies are installed by pip.

| Platform | Python | Native wheel |
| --- | --- | --- |
| Windows x64 | CPython 3.11–3.14 | `win_amd64` |

Rendering requires **desktop OpenGL 3.3+**, a compatible system graphics driver,
and a graphical session or an application-provided compatible context. NumPy
output still uses OpenGL. Version 1.0.0 supports Windows x64 only; Linux, macOS,
ARM, and free-threaded Python are outside the supported binary matrix.
PyPI contains wheels only, so pip
does not fall back to compiling this project on an unsupported platform.

Install an integration when needed:

```console
python -m pip install "python-projectm[glfw]"
python -m pip install "python-projectm[pyside6]"
```

The ModernGL adapter uses your application's existing ModernGL installation.
The default NumPy renderer creates a hidden GLFW window and needs the `glfw`
extra; it can also borrow an application's context. The PySide6 extra follows
Qt's own Windows system requirements.

## Quick start

After installing `python-projectm[glfw]`, run this from any directory:

```python
from importlib.resources import files

import glfw
import numpy as np

from python_projectm.integrations.glfw import GLFWRenderer

preset = files("python_projectm").joinpath("presets/pulse.milk").read_text(encoding="utf-8")
try:
    with GLFWRenderer(width=960, height=540) as renderer:
        renderer.load_preset_data(preset, smooth=False)
        with renderer.current():
            glfw.swap_interval(1)
        silence = np.zeros((512, 2), dtype=np.float32)
        while not renderer.should_close:
            renderer.poll_events()
            renderer.add_pcm(silence)
            renderer.render()
finally:
    glfw.terminate()
```

This uses the included original preset and silence to demonstrate rendering.
Applications supply PCM; the library does not capture or play audio. The
[runnable examples](https://github.com/serh11chyrva/python-projectm/blob/main/examples/README.md)
also provide continuous synthetic audio and streamed WAV input.

## Integrations

| Application needs | Entry point | Output |
| --- | --- | --- |
| Existing OpenGL context | `python_projectm.ProjectM` | Current or explicit framebuffer |
| GLFW window | `GLFWRenderer` | Existing or owned window |
| ModernGL composition | `ModernGLRenderer` | Texture or application framebuffer |
| PySide6 UI | `ProjectMWidget` | GPU rendering in a `QOpenGLWidget` |
| PySide6 worker rendering | `ThreadedProjectMWidget` | Shared GPU textures |
| NumPy frames | `NumpyRenderer` | Writable RGBA `uint8` arrays |

See the [integration guide](https://python-projectm.readthedocs.io/en/latest/integrations.html)
for imports, PCM formats, context ownership, thread rules, and cleanup.

## Development and licensing

[Source builds and editable installs](https://python-projectm.readthedocs.io/en/latest/source-build.html),
[contributing](https://github.com/serh11chyrva/python-projectm/blob/main/CONTRIBUTING.md),
[tests](https://github.com/serh11chyrva/python-projectm/blob/main/tests/README.md),
and the [release procedure](https://python-projectm.readthedocs.io/en/latest/publishing.html)
describe the development workflow.

Original binding code, the C++ wrapper, and the demo preset use the **MIT License**.
Bundled projectM is **LGPL-2.1-or-later**, and other native components retain their
own terms. See [third-party notices](https://github.com/serh11chyrva/python-projectm/blob/main/THIRD_PARTY_NOTICES.md)
and the [licensing guide](https://python-projectm.readthedocs.io/en/latest/licensing.html).
Corresponding native sources and rebuild scripts accompany every binary
[GitHub Release](https://github.com/serh11chyrva/python-projectm/releases).
