"""Qt offscreen rendering with commands queued to the owning render thread."""

import queue
import threading
import time

import numpy as np
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QOffscreenSurface, QOpenGLContext
from shiboken6 import delete

from python_projectm.core.validation import dimensions, integer
from python_projectm.integrations.numpy import NumpyRenderer
from python_projectm.integrations.pyside6.context import QtGLContext, opengl_format, require_gui_thread


class FrameEmitter(QObject):
    """Qt signals carrying worker frames, errors, and cleanup completion.

    ``frame_ready`` emits a NumPy RGBA frame, ``error`` emits an exception, and
    ``finished`` has no arguments. Connect frame consumers to GUI-thread slots.
    """

    frame_ready = Signal(object)
    error = Signal(object)
    finished = Signal()


class RenderThread(threading.Thread):
    """Create on the GUI thread; stop and join before destroying the application.

    The surface is created/destroyed on the GUI thread, while the GL context,
    projectM instance, and framebuffer live exclusively on the render thread.

    Args:
        width: Positive output width in physical pixels.
        height: Positive output height in physical pixels.
        emitter: Usually a :class:`FrameEmitter` created on the GUI thread.
        fps: Positive render-loop frame-rate target.

    Preset, PCM, and resize methods enqueue commands and can be called before
    ``start()``. The queue holds 128 commands; a full queue raises ``queue.Full``
    without blocking. Initialization or frame failures stop the worker; command
    errors are emitted while rendering continues. ``error`` retains the most
    recently reported exception and ``renderer`` is available only while active.
    """

    def __init__(self, width, height, emitter, fps=60):
        require_gui_thread()
        super().__init__(daemon=True)
        self.width, self.height = dimensions(width, height)
        self.fps = integer(fps, "fps")
        self.delay = 1.0 / self.fps
        self.emitter = emitter
        self.renderer: NumpyRenderer | None = None
        self.error: Exception | None = None
        self._stop_event = threading.Event()
        self._commands = queue.Queue(maxsize=128)
        self._surface = QOffscreenSurface()
        self._surface.setFormat(opengl_format())
        self._surface.create()
        if not self._surface.isValid():
            delete(self._surface)
            self._surface = None
            raise RuntimeError("Qt could not create the render thread's offscreen surface")

    def _report_error(self, error: Exception) -> None:
        self.error = error
        signal = getattr(self.emitter, "error", None)
        if signal is not None:
            signal.emit(error)

    def _enqueue(self, name, *args, **kwargs) -> None:
        if self._stop_event.is_set():
            raise RuntimeError("Render thread is stopped")
        self._commands.put_nowait((name, args, kwargs))

    def load_preset(self, preset_path, *, smooth: bool = True) -> None:
        """Queue a preset path or projectM URL, optionally with a smooth transition."""
        self._enqueue("load_preset_file", preset_path, smooth=smooth)

    load_preset_file = load_preset

    def load_preset_data(self, data: str, *, smooth: bool = True) -> None:
        """Queue Milkdrop source text for loading in the render thread's context."""
        self._enqueue("load_preset_data", data, smooth=smooth)

    def add_pcm(self, samples, channels: int | None = None) -> None:
        """Copy PCM before enqueueing it so the caller may reuse its input buffer."""
        self._enqueue("add_pcm", np.array(samples, copy=True, order="C"), channels)

    def resize(self, width: int, height: int) -> None:
        """Queue positive output dimensions; allocate replacements on the worker."""
        self._enqueue("resize", *dimensions(width, height))

    def run(self):
        """Run the worker loop; invoke through ``start()``, not directly from the GUI."""
        context = None
        renderer = None
        try:
            context = QOpenGLContext()
            context.setFormat(self._surface.format())
            if not context.create():
                raise RuntimeError("Qt could not create the render thread's OpenGL context")
            adapter = QtGLContext(context, self._surface)
            renderer = NumpyRenderer(self.width, self.height, context=adapter)
            self.renderer = renderer
            with renderer.current() as pm:
                pm.fps = self.fps
            next_frame = time.monotonic()
            while not self._stop_event.is_set():
                # Bound command work so producers cannot indefinitely delay rendering.
                for _ in range(128):
                    try:
                        name, args, kwargs = self._commands.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        getattr(renderer, name)(*args, **kwargs)
                        if name == "resize":
                            self.width, self.height = renderer.size
                    except Exception as error:
                        self._report_error(error)
                if self._stop_event.is_set():
                    break
                self.emitter.frame_ready.emit(renderer.render_frame())
                next_frame += self.delay
                remaining = next_frame - time.monotonic()
                if remaining < 0:
                    next_frame = time.monotonic()
                else:
                    self._stop_event.wait(remaining)
        except Exception as error:
            self._report_error(error)
        finally:
            self._stop_event.set()
            try:
                if renderer is not None:
                    renderer.close()
            except Exception as error:
                self._report_error(error)
            finally:
                self.renderer = None
                if context is not None:
                    context.doneCurrent()
                    # There is no Qt event loop here to process deleteLater().
                    delete(context)
                signal = getattr(self.emitter, "finished", None)
                if signal is not None:
                    signal.emit()

    def stop(self) -> None:
        """Request worker shutdown without waiting; follow with GUI-thread join()."""
        self._stop_event.set()

    def _release_surface(self) -> None:
        require_gui_thread()
        if self._surface is not None:
            self._surface.destroy()
            delete(self._surface)
            self._surface = None

    def join(self, timeout=None) -> None:
        """Wait for worker termination and release its surface on the GUI thread.

        With a timeout, the surface remains alive while the worker is running.
        Join again or call :meth:`close` before destroying the Qt application.
        """
        super().join(timeout)
        if not self.is_alive():
            self._release_surface()

    def close(self) -> None:
        """Stop, join, and destroy the offscreen surface on the GUI thread."""
        require_gui_thread()
        self.stop()
        if self.ident is not None:
            self.join()
        else:
            self._release_surface()
