# Quick start

Complete the [installation guide](installation.md) first. Run these snippets
from the repository root so `examples/presets/pulse.milk` resolves to the bundled
original preset. Native libraries must be available before creating a renderer.

## Open a GLFW window

Install the package's `glfw` extra as described in the installation guide.
Create the window, poll events, submit PCM, and render on the main thread:

```python
import glfw
import numpy as np

from python_projectm.integrations.glfw import GLFWRenderer

try:
    with GLFWRenderer(width=960, height=540) as renderer:
        renderer.load_preset_file("examples/presets/pulse.milk", smooth=False)
        with renderer.current() as pm:
            pm.fps = 60
            glfw.swap_interval(1)

        silence = np.zeros((512, 2), dtype=np.float32)
        while not renderer.should_close:
            renderer.poll_events()
            renderer.add_pcm(silence)
            renderer.render()
finally:
    glfw.terminate()
```

This example feeds silence to show the call sequence. Use the
[runnable examples](examples.md) for continuous synthetic or WAV PCM. Setting
`pm.fps` informs projectM; the application controls rendering and audio timing.
Call `glfw.terminate()` only when the application owns global GLFW lifetime.

## Read a NumPy frame

The default NumPy renderer owns a hidden GLFW window and also needs the `glfw`
extra and main-thread use:

```python
import glfw
import numpy as np

from python_projectm.integrations.numpy import NumpyRenderer

try:
    with NumpyRenderer(640, 360) as renderer:
        renderer.load_preset_file("examples/presets/pulse.milk", smooth=False)
        renderer.add_pcm(np.zeros((512, 2), dtype=np.float32))
        frame = renderer.render_frame()
        # frame: writable C-contiguous uint8 RGBA, shape (360, 640, 4).
        # The default origin is the top-left corner.
finally:
    glfw.terminate()
```

Pass a [context adapter](api/rendering.rst) to borrow a context instead of
creating a hidden window. Readback transfers rendered pixels into CPU memory;
it still requires a desktop OpenGL implementation.

## Use an application's OpenGL context

Make the application's desktop OpenGL 3.3+ context current before construction,
and keep the original context current for every core operation and cleanup:

```python
from python_projectm import ProjectM

# The application has made its own OpenGL context current here.
with ProjectM() as pm:
    pm.set_size(1280, 720)
    pm.load_preset_file("examples/presets/pulse.milk", smooth=False)
    pm.beat_sensitivity = 1.0
    pm.render()  # Render to the currently bound draw framebuffer.
```

`pm.render(framebuffer=fbo_id)` selects an explicit OpenGL framebuffer. Core
rendering does not swap buffers or poll events. A `with` statement closes
projectM before the application's context is destroyed.

See the [integration guide](integrations.md) for Qt widgets, background
rendering, ModernGL texture composition, PCM formats, and full lifetime rules.
