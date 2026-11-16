# Runnable examples

Build the native libraries and use the existing Python environment described in
the root [README.md](../README.md). Run these commands **from the repository root**
as modules; the examples share a small PCM source and a bundled original preset.
No preset download, texture pack, audio device, or image-writing package is needed.

| Integration | Module | Additional Python package | Result |
| --- | --- | --- | --- |
| GLFW | `examples.glfw_visualizer` | Package's `glfw` extra | Resizable window; Escape closes it |
| NumPy | `examples.numpy_frames` | Package's `glfw` extra | Reused RGBA array and a final PPM image |
| ModernGL | `examples.moderngl_texture` | Application's `moderngl` installation | GPU texture consumed by a second shader, then a final PPM image |

```powershell
.venv/Scripts/python.exe -m examples.glfw_visualizer
.venv/Scripts/python.exe -m examples.numpy_frames --frames 120
.venv/Scripts/python.exe -m examples.moderngl_texture --frames 120
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

`presets/pulse.milk` was written for these examples and uses no external assets;
it shares the repository's MIT license. Other presets may have their own licenses
and texture requirements. Presets placed directly in `examples/` remain local;
the `examples/presets/` directory contains the versioned demonstration preset.
Generated images in `examples/output/` are ignored by Git.
