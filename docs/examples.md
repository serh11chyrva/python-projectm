# Runnable examples

The `examples/` package contains complete applications using an original preset
and a shared PCM source. Prepare the checkout's editable environment using
the [source guide](source-build.md). Run all commands
from the repository root.

| Integration | Command | Additional dependency |
| --- | --- | --- |
| GLFW window | `uv run --locked --extra glfw python -m examples.glfw_visualizer` | Package's `glfw` extra |
| NumPy frame export | `uv run --locked --extra glfw python -m examples.numpy_frames --frames 120` | Package's `glfw` extra |
| ModernGL composition | `.venv/Scripts/python.exe -m examples.moderngl_texture --frames 120` | Application's `moderngl` installation |
| PySide6 studio | `uv run --locked --extra pyside6 python -m examples.pyside6_visualizer` | Package's `pyside6` extra |

The ModernGL adapter borrows an application-supplied ModernGL installation;
the repository does not declare a ModernGL extra. See the
[examples README](https://github.com/serh11chyrva/python-projectm/blob/main/examples/README.md)
for platform notes and full command-line usage.

## Audio and presets

Examples generate continuous stereo PCM unless `--wav path/to/audio.wav` is
supplied. WAV input supports uncompressed 8-bit or 16-bit mono/stereo PCM and
loops while rendering. Audio is analyzed for visualization without playback,
microphone capture, or system-audio capture.

Common arguments include `--preset`, `--wav`, `--width`, `--height`, `--fps`,
and `--frames`. The packaged `python_projectm/presets/pulse.milk` needs no texture pack
or download. Other presets can have separate assets and licensing requirements.

## Frame export

NumPy and ModernGL examples accept `--output path/to/frame.ppm` and write an
uncompressed RGB image after a finite run. Their default is 120 frames.
Generated output under `examples/output/` is ignored by Git.

## PySide6 studio

The studio supports preset selection, smooth transitions, looping WAV input,
synthetic PCM, input gain, pause/resume, statistics, and PNG snapshots.

```powershell
uv run --locked --extra pyside6 python -m examples.pyside6_visualizer --mode gpu
uv run --locked --extra pyside6 python -m examples.pyside6_visualizer --mode worker --fps 30
```

GPU mode renders into `QOpenGLWidget`'s backing framebuffer. Worker mode owns
a Qt offscreen context on the rendering thread and sends copied NumPy frames
to the GUI. Both paths use Qt and need neither GLFW nor ModernGL.

For a finite run with a snapshot:

```powershell
uv run --locked --extra pyside6 python -m examples.pyside6_visualizer --frames 60 --screenshot examples/output/qt.png
```

The example stops timers and closes projectM while its context exists. Worker
mode stops and joins the renderer before destroying the GUI-owned surface.
