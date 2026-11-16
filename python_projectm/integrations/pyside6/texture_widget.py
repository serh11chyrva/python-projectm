"""Present worker-rendered projectM textures without reading pixels into Python."""

import queue
import threading
from contextlib import contextmanager

from OpenGL import GL
from PySide6.QtCore import QEvent, QTimer, Signal, Slot
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication

from python_projectm.core.validation import integer
from python_projectm.integrations.pyside6.context import opengl_format, require_gui_thread
from python_projectm.integrations.pyside6.pcm_queue import PCMBufferPool
from python_projectm.integrations.pyside6.render_thread import FrameEmitter
from python_projectm.integrations.pyside6.shared_texture import TextureRenderThread, frame_fence, wait_fence


class ThreadedProjectMWidget(QOpenGLWidget):
    """Render projectM on a worker and present shared textures on the GUI thread.

    ``fps`` is a positive worker frame-rate target. ``preset`` optionally queues
    the initial preset path. The widget owns the worker, its offscreen surface,
    three output textures, and a GUI-local read framebuffer. Cleanup joins the
    worker before Qt destroys the sharing context.

    Create/access the widget and its ``fps`` property on the GUI thread. Preset
    and PCM methods may be called by producers, including before initialization.
    Their bounded 128-command queue raises ``queue.Full`` instead of blocking.
    PCM is copied into reusable storage and stays owned until consumed. The
    worker's core/context must never be accessed directly from the GUI thread.

    ``initialized`` is emitted after the first texture is drawn, ``frame_rendered``
    after a texture blit, and ``error`` carries initialization/command/render
    exceptions. Use Qt's ``frameSwapped`` signal for presentation statistics.
    """

    initialized = Signal()
    frame_rendered = Signal()
    error = Signal(object)

    def __init__(self, parent=None, *, fps: int = 60, preset=None):
        super().__init__(parent)
        format = opengl_format()
        format.setSamples(0)
        self.setFormat(format)
        self._fps = integer(fps, "fps")
        self._commands = queue.Queue(maxsize=128)
        self._pcm_buffers = PCMBufferPool()
        self._lifecycle = threading.RLock()
        self._worker = None
        self._emitter = None
        self._native_context = None
        self._read_fbo = 0
        self._requested_size = None
        self._preset = None
        self._restore_preset = None
        self._initialized = False
        self._initialization_failed = False
        self._cleaning = False
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(75)
        self._resize_timer.timeout.connect(self._resize_worker)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.cleanup)
        if parent is not None:
            parent.destroyed.connect(self.cleanup)
        if preset is not None:
            self.load_preset_file(preset)

    @property
    def fps(self) -> int:
        """Positive worker frame-rate target; set on the GUI thread."""
        return self._fps

    @fps.setter
    def fps(self, value: int) -> None:
        require_gui_thread()
        value = integer(value, "fps")
        with self._lifecycle:
            if self._worker is not None:
                self._worker.set_fps(value)
            self._fps = value

    def _enqueue(self, name, *args, **kwargs):
        with self._lifecycle:
            if self._worker is not None and self._worker._stop_event.is_set():
                raise RuntimeError("The shared-texture render worker is stopped")
            command = (name, args, kwargs)
            self._commands.put_nowait(command)
            if name in ("load_preset_file", "load_preset_data"):
                self._preset = command

    def load_preset_file(self, path, *, smooth: bool = True) -> None:
        """Queue a preset path for the worker's context."""
        self._enqueue("load_preset_file", path, smooth=smooth)

    load_preset = load_preset_file

    def load_preset_data(self, data: str, *, smooth: bool = True) -> None:
        """Queue Milkdrop source text for the worker's context."""
        self._enqueue("load_preset_data", data, smooth=smooth)

    def add_pcm(self, samples, channels: int | None = None) -> None:
        """Copy PCM once; the producer may immediately reuse its input buffer."""
        buffer = self._pcm_buffers.copy(samples)
        try:
            self._enqueue("add_pcm", buffer, channels)
        except Exception:
            self._pcm_buffers.release(buffer)
            raise

    def _pixel_size(self):
        ratio = self.devicePixelRatioF()
        return max(1, int(self.width() * ratio + 0.5)), max(1, int(self.height() * ratio + 0.5))

    def initializeGL(self):
        """Start a sharing worker after Qt creates the widget's native context."""
        if self._worker is not None:
            return
        self._initialization_failed = False
        try:
            with self._lifecycle:
                self._native_context = self.context()
                self._native_context.aboutToBeDestroyed.connect(self.cleanup)
                self._read_fbo = int(GL.glGenFramebuffers(1))
                self._emitter = FrameEmitter(self)
                self._emitter.frame_ready.connect(self._on_frame_ready)
                self._emitter.error.connect(self._on_error)
                self._emitter.finished.connect(self._on_finished)
                self._requested_size = self._pixel_size()
                self._worker = TextureRenderThread(
                    *self._requested_size, self._emitter, fps=self._fps,
                    share_context=self._native_context, commands=self._commands,
                    pcm_buffers=self._pcm_buffers, startup_preset=self._restore_preset,
                )
                self._restore_preset = None
                self._worker.start()
        except Exception as error:
            self.cleanup()
            self._initialization_failed = True
            self.error.emit(error)

    @Slot(object)
    def _on_frame_ready(self, _):
        if self.sender() == self._emitter and self._worker is not None:
            self._worker.mailbox.notification_received()
            self.update()

    @Slot(object)
    def _on_error(self, error):
        if self.sender() == self._emitter:
            self.error.emit(error)

    @Slot()
    def _on_finished(self):
        if self.sender() == self._emitter and self._worker is not None and not self._cleaning:
            if self._worker.error is None:
                self.error.emit(RuntimeError("The shared-texture render worker stopped"))

    def resizeGL(self, width, height):
        """Coalesce physical-pixel resize commands while Qt resizes its own FBO."""
        self._resize_timer.start()

    @Slot()
    def _resize_worker(self):
        if self._worker is None or self._cleaning:
            return
        size = self._pixel_size()
        if size == self._requested_size:
            return
        try:
            self._worker.resize(*size)
            self._requested_size = size
        except queue.Full:
            self._resize_timer.start()
        except Exception as error:
            self.error.emit(error)

    def paintGL(self):
        """Blit the newest shared texture into Qt's current backing framebuffer."""
        if self._worker is None and not self._initialization_failed:
            self.initializeGL()
        if self._worker is None:
            return
        try:
            if self._pixel_size() != self._requested_size and not self._resize_timer.isActive():
                self._resize_timer.start()
            drawn = False
            with self._worker.mailbox.reading() as (slot, ready):
                if slot is None:
                    GL.glClearColor(0, 0, 0, 1)
                    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
                    return
                wait_fence(ready)
                read = int(GL.glGetIntegerv(GL.GL_READ_FRAMEBUFFER_BINDING))
                scissor = bool(GL.glIsEnabled(GL.GL_SCISSOR_TEST))
                try:
                    GL.glDisable(GL.GL_SCISSOR_TEST)
                    GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self._read_fbo)
                    GL.glFramebufferTexture2D(
                        GL.GL_READ_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0,
                        GL.GL_TEXTURE_2D, slot.texture_id, 0,
                    )
                    GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
                    GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, int(self.defaultFramebufferObject()))
                    width, height = self._pixel_size()
                    GL.glBlitFramebuffer(
                        0, 0, slot.width, slot.height, 0, 0, width, height,
                        GL.GL_COLOR_BUFFER_BIT, GL.GL_LINEAR,
                    )
                    drawn = True
                finally:
                    GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, read)
                    if scissor:
                        GL.glEnable(GL.GL_SCISSOR_TEST)
                    consumed = frame_fence()
                    if slot.read_fence is not None:
                        GL.glDeleteSync(slot.read_fence)
                    slot.read_fence = consumed
            if drawn:
                if not self._initialized:
                    self._initialized = True
                    self.initialized.emit()
                self.frame_rendered.emit()
        except Exception as error:
            self._worker.stop()
            self.error.emit(error)

    @contextmanager
    def _current(self):
        previous = QOpenGLContext.currentContext()
        surface = previous.surface() if previous is not None else None
        unchanged = previous == self.context()
        try:
            if not unchanged:
                self.makeCurrent()
            if QOpenGLContext.currentContext() != self.context():
                raise RuntimeError("Qt could not activate the widget context for cleanup")
            yield
        finally:
            if not unchanged:
                if previous is not None and surface is not None:
                    if not previous.makeCurrent(surface):
                        raise RuntimeError("Qt could not restore the preceding OpenGL context")
                else:
                    self.doneCurrent()

    @Slot()
    def cleanup(self) -> None:
        """Detach GUI resources and join the worker before losing the context."""
        require_gui_thread()
        if self._cleaning:
            return
        self._cleaning = True
        self._resize_timer.stop()
        try:
            with self._lifecycle:
                worker = self._worker
                try:
                    if self._read_fbo:
                        with self._current():
                            GL.glDeleteFramebuffers(1, [self._read_fbo])
                finally:
                    self._read_fbo = 0
                    if worker is not None:
                        worker.close()
                    self._worker = None
                    while True:
                        try:
                            name, args, _ = self._commands.get_nowait()
                        except queue.Empty:
                            break
                        if name == "add_pcm":
                            self._pcm_buffers.release(args[0])
                    self._pcm_buffers.clear()
                self._initialized = False
                self._initialization_failed = False
                self._restore_preset = self._preset
        except Exception as error:
            self.error.emit(error)
        finally:
            if self._native_context is not None:
                try:
                    self._native_context.aboutToBeDestroyed.disconnect(self.cleanup)
                except (RuntimeError, TypeError):
                    pass
                self._native_context = None
            if self._emitter is not None:
                self._emitter.deleteLater()
                self._emitter = None
            self._cleaning = False

    def closeEvent(self, event):
        """Stop the owned worker before Qt closes the widget."""
        self.cleanup()
        super().closeEvent(event)

    def event(self, event):
        """Release the sharing worker before deferred deletion or reparenting."""
        if hasattr(self, "_resize_timer") and event.type() in (
            QEvent.Type.DeferredDelete, QEvent.Type.ParentAboutToChange
        ):
            self.cleanup()
        return super().event(event)
