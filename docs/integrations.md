# Rendering integrations

All renderers use the same `ProjectM` core. The native libraries must be built
together through the root CMake project; see the [installation guide](installation.md) for
installation and build instructions. Native loading is deferred until the first
native call, so importing an adapter does not load the native wrapper library.

The [runnable examples](examples.md) cover all four integrations with
an original preset and synthetic or WAV PCM. In particular,
[`pyside6_visualizer.py`](https://github.com/serh11chyrva/python-projectm/blob/main/examples/pyside6_visualizer.py) demonstrates both the
direct GPU widget and background Qt/NumPy rendering, with interactive controls,
frame export, resize handling, error reporting, and explicit shutdown.

| Adapter | Owns | Application retains ownership of |
| --- | --- | --- |
| `ProjectM` | Native projectM instance | Current GL context |
| `Renderer` | ProjectM instance | Supplied context adapter |
| `GLFWRenderer` | ProjectM and a window if none was passed | Existing windows and GLFW global lifetime |
| `ModernGLRenderer` | ProjectM, output texture and framebuffer | ModernGL context and external target framebuffers |
| `NumpyRenderer` | ProjectM, RGBA8 framebuffer, and its default hidden GLFW window | A supplied context adapter and any `out` array |
| `ProjectMWidget` | ProjectM and repaint timer | Qt application and widget lifecycle |
| `QtOffscreenContext` | Qt context and offscreen surface | Qt application |
| `RenderThread` | Qt offscreen surface, worker context and NumPy renderer | GUI-thread creation, shutdown, and signal connections |
| `ThreadedProjectMWidget` | Sharing worker, three GPU textures, GUI-local read FBO | GUI-thread widget creation and shutdown |

## Context and resource rules

projectM requires **desktop OpenGL 3.3 or newer**. NumPy output is a GPU-to-CPU
readback, not an implementation of projectM without OpenGL. CPU-only machines
need an appropriate software OpenGL driver.

A core instance and its GL resources belong to the thread and native context in
which they were created. Core operations, including audio submission and
destruction, check both. Shared contexts are not interchangeable: framebuffer
and vertex-array objects belong to a specific context.

Use `close()` or a `with` statement before destroying the GL context. `close()`
is idempotent. A destructor only attempts native cleanup when the owning thread
and context are still available; it cannot safely recover a lost context.
Closing an adapter does not close a borrowed context or terminate GLFW.

Managed renderer operations activate their supplied context. Use
`with renderer.current() as pm:` to change core parameters or call other core
methods. `with renderer:` controls renderer lifetime; it does not keep the
context current between method calls. GLFW and Qt adapters restore a preceding
context from the same toolkit. Do not switch between unrelated toolkit context
providers inside their active scopes.

By default rendering preserves the framebuffer bindings, viewport, shader
program, VAO, array/pixel buffers, textures/samplers, blend state, color masks,
and other GL state used by projectM. `preserve_state=False` skips per-frame state
preservation for applications that own the rendering state; explicitly rebind
all state needed by subsequent drawing. Do not render projectM inside an active
transform-feedback operation or an application query.

Rebuilt wrappers perform frame preparation, viewport setup, state preservation,
and rendering in one native call. Success does not require a second error-query
call. GL limits and snapshot storage are cached in the owning context; only the
fragment texture units that projectM can use are visited. Unchanged output sizes
are not submitted again. Existing wrapper DLLs fall back to the original Python
rendering path automatically. Rebuild using the root README to enable the native
frame operation; no dependency change is required.

On EGL systems, select the matching PyOpenGL platform **before importing**
`python_projectm` or `OpenGL`, for example `PYOPENGL_PLATFORM=egl`. The context
must expose desktop OpenGL, not OpenGL ES. Linux/macOS native changes have not
been verified by a build.

## Shared core API

An existing context must be current before creating `ProjectM`:

```python
from python_projectm import ProjectM

# Your application has already made its OpenGL context current here.
with ProjectM() as pm:
    pm.set_size(1280, 720)
    pm.load_preset_file("preset.milk", smooth=False)
    pm.fps = 60
    pm.beat_sensitivity = 1.0
    pm.preset_duration = 30.0
    pm.soft_cut_duration = 3.0
    pm.hard_cut_enabled = False
    pm.aspect_correction = True
    pm.mesh_size = (48, 36)
    pm.set_texture_search_paths(["textures"])
    pm.render()  # Uses the currently bound draw framebuffer.
    # pm.render(framebuffer=application_fbo) also accepts an explicit GL ID.
```

`load_preset_data(text)` loads Milkdrop source held in a string.
Preset failures become `ProjectMError` with the upstream error message.
`idle://` URLs remain available through `load_preset_file`.
Additional parameters are `hard_cut_duration`, `hard_cut_sensitivity`,
`preset_locked`, and `easter_egg`; `reset_textures()` reloads texture resources.
Sizes passed to the core may be zero to suspend rendering. Allocated texture
and NumPy output dimensions must be positive.

`ProjectM` remains available from `python_projectm.core`, and the existing
`ProjectMCore`, mixins, `FBO`, `ViewportGuard`, and Qt integration imports remain
available.

### PCM audio

The core and managed renderers accept:

- Floating-point arrays, normally in [-1, 1], through `add_pcm_float`.
- Signed 16-bit PCM through `add_pcm_int16`.
- Unsigned 8-bit PCM with silence at 128 through `add_pcm_uint8`.
- Automatic dispatch for those dtypes through `add_pcm`.

Use `(frames, 1)` or `(frames, 2)` arrays to infer channels. A one-dimensional
array defaults to mono; pass `channels=2` for flat interleaved stereo.
Planar stereo `(2, frames)` is not accepted. Noncontiguous input is copied.
The count sent to C is the number of frames per channel. Large blocks are split
at `pcm_max_samples()`; projectM retains its rolling audio history.
Audio is analyzed for visualization; these bindings do not capture, play,
resample, or schedule an audio stream.

```python
import numpy as np

stereo = np.zeros((512, 2), dtype=np.float32)
renderer.add_pcm(stereo)
# In an audio callback, enqueue a copy to the render thread instead.
```

## GLFW

The `glfw` optional dependency is required. Create and close GLFW windows and
poll events on the main thread. Existing window callbacks are left in place;
framebuffer dimensions are queried for every frame, including high-DPI changes.
Minimized windows are skipped.

```python
import glfw
from python_projectm.integrations.glfw import GLFWRenderer

try:
    with GLFWRenderer(width=1280, height=720) as renderer:
        renderer.load_preset_file("preset.milk", smooth=False)
        with renderer.current() as pm:
            pm.fps = 60
            glfw.swap_interval(1)
        while not renderer.should_close:
            renderer.poll_events()
            renderer.render()  # Renders and swaps buffers.
finally:
    glfw.terminate()  # Only when this application owns global GLFW lifetime.
```

Pass `GLFWRenderer(existing_window)` to borrow a window. Its context must not be
current on another thread. The renderer does not destroy a borrowed window.
Use `render(swap_buffers=False)` when your application controls presentation.

`GLFWContext(existing_window)` adapts just the context. A default
`GLFWContext(width=..., height=..., visible=False)` owns a hidden window.
Creating an owned window sets and resets GLFW's global window hints. Create a
window yourself when you need custom hints.

## ModernGL

The application supplies an already installed ModernGL library and context;
the adapter does not import ModernGL or create a second native context.

```python
import moderngl
from python_projectm.integrations.moderngl import ModernGLRenderer

ctx = moderngl.create_standalone_context(require=330)
try:
    with ModernGLRenderer(ctx, 1280, 720) as renderer:
        renderer.load_preset_file("preset.milk", smooth=False)
        texture = renderer.render()  # A regular ModernGL RGBA8 texture.
        # texture.use(location=0) lets your own shader consume it.
        # renderer.framebuffer can be used with ctx.copy_framebuffer(...).
        # renderer.render(application_framebuffer) borrows another target.
finally:
    ctx.release()
```

The native context must be current for construction, operations, and cleanup.
For an application that switches contexts, pass `activate=adapter.current`,
where `adapter` is a `GLFWContext`, `QtGLContext`, or another object whose
`current()` method restores the preceding native context.
For a standalone ModernGL context, `activate=lambda: ctx` uses ModernGL's own
activation context manager; follow its backend's context-restoration rules.
Detected ModernGL contexts cannot activate their toolkit-owned context.

`resize(width, height)` replaces the owned texture and framebuffer; references
to the preceding output resources become invalid. External framebuffer targets
must belong to the supplied ModernGL context and are never released by the
renderer.

## NumPy frames in CPU memory

Without a `context` argument, `NumpyRenderer` creates a hidden GLFW window and
therefore requires the `glfw` extra and main-thread use.

```python
import glfw
import numpy as np
from python_projectm.integrations.numpy import NumpyRenderer

try:
    with NumpyRenderer(640, 360) as renderer:
        renderer.load_preset_file("preset.milk", smooth=False)
        renderer.add_pcm_float(np.zeros((512, 2), dtype=np.float32))
        frame = renderer.render_frame()
        assert frame.shape == (360, 640, 4)
        assert frame.dtype == np.uint8

        reusable = np.empty_like(frame)
        renderer.render_frame(out=reusable)
finally:
    glfw.terminate()
```

Each result is writable and C-contiguous RGBA8 with a top-left origin.
Use `flip_y=False` to retain OpenGL's bottom-left origin. An `out` array must be
writable C-contiguous `uint8` of shape `(height, width, 4)`; it is returned
directly. After `resize`, allocate an output array of the new shape.

To borrow ModernGL, use
`context=ModernGLContext(ctx, width, height, activate=...)`. To borrow Qt, pass
a `QtGLContext`. A custom adapter needs `make_current()`, `done_current()`,
and `get_size()`; it may provide a restoring `current()` context manager.

## PySide6

PCM submission keeps the owning context current without saving or changing GL
state. Audio commands do not request extra repaints; the rendering scheduler
controls animation independently of the audio producer. The native PCM block
limit is cached per projectM instance after its first successful query.

`ProjectMWidget` schedules single-shot precise timers against monotonic frame
deadlines after Qt's `frameSwapped` signal. The target is subject to the display's
refresh rate, composition, and rendering cost. `frame_rendered` reports completed
render calls; use the inherited `frameSwapped` signal to count presentations.

Only the `pyside6` optional dependency is needed for the Qt-native paths.
Qt objects require an existing `QApplication` or `QGuiApplication`.

### Shared-texture GPU worker

Use `ThreadedProjectMWidget` when projectM rendering should run outside the GUI
thread without transferring RGBA frames to CPU memory:

```python
from python_projectm.integrations.pyside6 import ThreadedProjectMWidget

# Configure QSurfaceFormat and create QApplication as in the widget example below.
widget = ThreadedProjectMWidget(fps=60, preset="preset.milk")
widget.error.connect(lambda error: print(f"projectM: {error}"))
widget.resize(960, 540)
widget.show()
# Producers may call widget.add_pcm(samples); close/cleanup on the GUI thread.
```

The worker owns projectM, its context, and three texture/FBO pairs. Qt presents
the newest texture with a GPU framebuffer blit through a separate GUI-local FBO;
FBO names are never shared across contexts. Producer and consumer fences are
flushed before handoff, and GPU waits protect both reads and reuse. If every
slot is still in flight, the worker skips that output opportunity instead of
building an unbounded GPU backlog. A busy/hidden GUI has at most one outstanding
frame notification, and obsolete ready frames may be replaced.

The 128-command queue preserves PCM order and raises `queue.Full` when full.
PCM is copied once into pooled native-dtype storage, which is reused only after
consumption. Resize commands are coalesced; textures are replaced only after the
previous GUI reads finish. The `fps` property updates worker pacing and projectM.
This widget has no GUI-thread core access. Its `initialized` signal follows the
first texture blit; `frameSwapped` measures presentations. `grabFramebuffer()`
still reads pixels for an explicitly requested screenshot.

Call `cleanup()` or close the widget before destroying Qt. Cleanup detaches the
GUI FBO and joins the worker before releasing the sharing context. Qt context
recreation restarts the worker and restores the last requested preset. Existing
`ProjectMWidget`, `RenderThread`, and `NumpyViewport` APIs remain available.

### Direct GPU widget

```python
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication
from python_projectm.integrations.pyside6 import ProjectMWidget

format = QSurfaceFormat()
format.setVersion(3, 3)
format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
QSurfaceFormat.setDefaultFormat(format)  # Before QApplication.

app = QApplication([])
widget = ProjectMWidget(fps=60, preset="preset.milk")
widget.error.connect(lambda error: print(f"projectM: {error}"))
widget.resize(1280, 720)
widget.show()
app.exec()
```

The widget renders into `defaultFramebufferObject()`, respecting Qt's backing
FBO and device pixel ratio. Preset and PCM methods may be called before GL
initialization or from worker threads; Qt delivers these commands on the GUI
thread. Submitted PCM is copied so a producer may reuse its buffer. Command
failures are reported by the `error` signal. `initialized` and
`frame_rendered` are also available.
The public `pm` reference is `None` until initialization; direct core access
uses `with widget.current() as pm:` on the GUI thread to make the widget's
context current and restore the preceding Qt context afterward.

Cleanup is connected to context destruction, application shutdown, the supplied
parent's destruction, deferred widget deletion, and widget close events. Call
`cleanup()` before any other explicit native widget deletion. Do not destroy
the context first.

### Qt offscreen rendering on the GUI thread

```python
from PySide6.QtGui import QGuiApplication
from python_projectm.integrations.numpy import NumpyRenderer
from python_projectm.integrations.pyside6 import QtOffscreenContext

app = QGuiApplication([])
with QtOffscreenContext() as context:
    with NumpyRenderer(640, 360, context=context) as renderer:
        renderer.load_preset_file("preset.milk", smooth=False)
        frame = renderer.render_frame()
```

### Background rendering and CPU display

```python
from PySide6.QtWidgets import QApplication
from python_projectm.integrations.pyside6 import FrameEmitter, NumpyViewport, RenderThread

app = QApplication([])
viewport = NumpyViewport(keep_aspect=True)
viewport.resize(960, 540)
emitter = FrameEmitter()
emitter.frame_ready.connect(viewport.set_frame)
emitter.error.connect(lambda error: print(f"projectM: {error}"))

thread = RenderThread(960, 540, emitter, fps=60)  # Construct on the GUI thread.
thread.load_preset("preset.milk", smooth=False)  # Queued even before start().
app.aboutToQuit.connect(thread.close)
thread.start()
viewport.show()
app.exec()
```

`load_preset`, `load_preset_data`, `add_pcm`, and `resize` queue commands;
no caller directly operates on the worker's GL context. The command queue is
bounded to 128 items and raises `queue.Full` rather than blocking a producer.
Command errors emit `emitter.error` and leave rendering active; initialization
or frame failures stop the worker and are retained in `thread.error`.
`emitter.finished` is emitted after worker cleanup.

`RenderThread` keeps its private context current for the render loop and skips
per-frame state snapshots. Submitted PCM is copied into reusable native-dtype
buffers, which return to the pool after consumption. Call `set_fps(value)` to
queue a change to both worker pacing and projectM's frame-rate setting.
Connect frame signals to GUI-thread slots and keep consumers fast enough for
the selected frame rate.

For manual shutdown call `stop()` and then `join()` from the GUI thread, or use
`close()`. Waiting for the worker ensures projectM is destroyed in its own
current context before the GUI thread destroys the offscreen surface.
The legacy `GLFWProjectMCPURenderer` import remains available and uses the
default GLFW-backed `NumpyRenderer`; new Qt code can use the Qt-native paths.

## Native implementation details

The C header, C++ wrapper and ctypes declarations keep the existing C entry
points and add error reporting, explicit framebuffer rendering, texture paths,
additional parameters, and string deallocation. Windows GLEW initialization
runs in `pypm_create` after a GL context is current. Version strings are copied
and freed using projectM's allocator.

projectM 4.1.6 unconditionally binds framebuffer zero for final composition.
`cmake/ProjectMFramebuffer.cmake` reads its `ProjectM.cpp`, verifies the expected
source fragments, writes a build-directory copy that remembers the caller's
draw framebuffer, and substitutes that file in `projectM_main`. It changes no
class layouts, function signatures, or upstream source files. The wrapper and
that adapted projectM binary must be deployed together. Older wrapper binaries
report a missing-symbol error with a rebuild instruction.

For an application-managed deployment, set `PYTHON_PROJECTM_LIBRARY` to the
wrapper's full path before the first native call. Keep its matching projectM
runtime libraries beside it. The loaded library is cached for the process;
changing this variable after loading does not switch existing instances.

Reference behavior:
[projectM 4.1.6 rendering](https://github.com/projectM-visualizer/projectm/blob/v4.1.6/src/libprojectM/ProjectM.cpp),
[Qt OpenGL widget lifecycle](https://doc.qt.io/qtforpython-6/PySide6/QtOpenGLWidgets/QOpenGLWidget.html),
[GLFW thread rules](https://www.glfw.org/docs/latest/intro_guide.html#thread_safety),
[ModernGL contexts](https://moderngl.readthedocs.io/en/stable/reference/context.html).
