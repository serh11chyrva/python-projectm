# Runnable examples

Prepare the editable Python environment described in the
[source guide](../docs/source-build.md). Run these commands **from the repository root**
as modules; the examples share a small PCM source and a bundled original preset.
No preset download, texture pack, audio device, or image-writing package is needed.

| Integration | Module | Additional Python package | Result |
| --- | --- | --- | --- |
| GLFW | `examples.glfw_visualizer` | Package's `glfw` extra | Resizable window; Escape closes it |
| NumPy | `examples.numpy_frames` | Package's `glfw` extra | Reused RGBA array and a final PPM image |
| ModernGL | `examples.moderngl_texture` | Application's `moderngl` installation | GPU texture consumed by a second shader, then a final PPM image |
| PySide6 | `examples.pyside6_visualizer` | Package's `pyside6` extra | Interactive GPU widget or background Qt/NumPy rendering |

```powershell
.venv/Scripts/python.exe -m examples.glfw_visualizer
.venv/Scripts/python.exe -m examples.numpy_frames --frames 120
.venv/Scripts/python.exe -m examples.moderngl_texture --frames 120
.venv/Scripts/python.exe -m examples.pyside6_visualizer
```

The ModernGL example does not need GLFW. It creates a standalone desktop OpenGL
3.3 context and owns that context's lifetime. For an EGL backend on Linux, set
`PYOPENGL_PLATFORM=egl` before starting Python and pass `--backend egl`.
The GLFW and default NumPy examples own global GLFW lifetime and terminate it
after closing all projectM resources.

Common options are `--preset path/to/preset.milk`, `--wav path/to/audio.wav`,
`--width 960`, `--height 540`, `--fps 60`, and `--frames N`. Windowed examples run
until closed by default; image examples default to 120 frames. `--frames 0` runs
until interrupted. NumPy and ModernGL accept `--output path/to/frame.ppm`.
PPM is an uncompressed RGB image format; RGBA remains available inside Python.

PCM is generated as a continuous synthetic stereo signal unless `--wav` is given.
WAV input streams and loops uncompressed 8-bit or 16-bit mono/stereo PCM without
loading the entire file. All examples submit audio for visualization only; they
do not play sound, capture the microphone, or capture system audio. The small
timer-paced audio source demonstrates the submission API rather than an audio
playback clock. A real audio callback should hand copies to the rendering thread.

The packaged `python_projectm/presets/pulse.milk` was written for these examples and uses no external assets;
it shares the repository's MIT license. Other presets may have their own licenses
and texture requirements. Presets placed directly in `examples/` remain local;
the demonstration preset is resolved through the installed package's resources.
Generated images in `examples/output/` are ignored by Git.

## PySide6 studio

```powershell
# Direct rendering into QOpenGLWidget's framebuffer (default).
.venv/Scripts/python.exe -m examples.pyside6_visualizer --mode gpu

# Render on a worker and present shared GPU textures without CPU frame copies.
.venv/Scripts/python.exe -m examples.pyside6_visualizer --mode threaded --fps 60

# Qt offscreen context on a render worker; RGBA frames arrive on the GUI thread.
.venv/Scripts/python.exe -m examples.pyside6_visualizer --mode worker --fps 30

# A finite run with a PNG snapshot and a nonzero exit code on errors.
.venv/Scripts/python.exe -m examples.pyside6_visualizer --frames 60 --screenshot examples/output/qt.png
```

The window provides preset selection, smooth transitions, looping PCM WAV input,
a synthetic stereo source, input gain, PCM pause/resume, a PNG frame exporter,
rendering statistics, and visible nonmodal error messages. Space toggles PCM
pause, Ctrl+O opens a preset, Ctrl+Shift+O opens WAV, Ctrl+S saves a frame, and
Escape closes the window. Pausing feeds silence and retains the source position;
the visualization itself continues animating. The frame-rate target is chosen
with `--fps` at launch.

GPU statistics count Qt's `frameSwapped` presentations; CPU worker statistics
count received frames, which may be coalesced before painting. Rendering targets
do not guarantee the same display rate. The GPU widget schedules against
monotonic deadlines instead of rounding 60 FPS to a repeating 17 ms interval.

All modes use Qt-native contexts and need no GLFW or ModernGL installation.
The surface format is selected before creating `QApplication`. GPU commands go
through `ProjectMWidget`; the example never issues a core call from an audio
producer. Worker mode submits preset, copied PCM, and debounced physical-pixel
resize commands through `RenderThread`'s bounded queue. It drops a PCM block
rather than blocking the GUI when that queue is full. `NumpyViewport` consumes
frames on the GUI thread, and screenshots detach their `QImage` from NumPy memory.

Threaded GPU mode uses `ThreadedProjectMWidget` with three shared textures and
fences for producer/consumer ownership. The GUI blits the latest texture; it does
not receive NumPy frames. Notifications are coalesced, in-flight GPU work is
bounded by the texture slots, and PCM buffers are pooled until consumed. The
original `worker` mode remains available for applications that need CPU frames.

Closing the window or quitting the application stops the PCM timer first. GPU
mode cleans up projectM while the widget context exists. Worker mode stops and
joins the render thread before destroying the GUI-owned offscreen surface. A
15-second startup watchdog reports context initialization failures. Finite runs
also close with an error status when a preset, render, or snapshot operation fails.
Ordinary interactive runs keep the window open so a bad input can be replaced.

The lifecycle follows the [Qt OpenGL widget documentation](https://doc.qt.io/qtforpython-6/PySide6/QtOpenGLWidgets/QOpenGLWidget.html).
For the adapter API and context ownership rules, see [docs/integrations.md](../docs/integrations.md).
