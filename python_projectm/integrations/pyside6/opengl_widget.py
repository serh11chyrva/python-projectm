"""A QOpenGLWidget that renders projectM directly into Qt's backing framebuffer."""

from contextlib import contextmanager

import numpy as np
from PySide6.QtCore import QEvent, QTimer, Signal, Slot
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication

from python_projectm.core import ProjectM
from python_projectm.core.validation import integer
from python_projectm.gl.state import GLStateGuard
from python_projectm.integrations.pyside6.context import opengl_format, require_gui_thread


class ProjectMWidget(QOpenGLWidget):
    """A GPU viewport; PCM and preset commands can also be submitted from workers."""

    initialized = Signal()
    frame_rendered = Signal()
    error = Signal(object)
    _command = Signal(object)

    def __init__(self, parent=None, *, fps: int = 60, preset=None):
        super().__init__(parent)
        self.setFormat(opengl_format())
        self.pm: ProjectM | None = None
        self._native_context = None
        self._pending = []
        self._preset = None
        self._initialization_failed = False
        self._fps = integer(fps, "fps")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._command.connect(self._apply_command)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.cleanup)
        if parent is not None:
            parent.destroyed.connect(self.cleanup)
        if preset is not None:
            self.load_preset_file(preset)

    @property
    def fps(self) -> int:
        return self._fps

    @fps.setter
    def fps(self, value: int) -> None:
        require_gui_thread()
        self._fps = integer(value, "fps")
        if self.pm is not None:
            self._apply_command(("__fps__", (self._fps,), {}))
            self._timer.start(max(1, round(1000 / self._fps)))

    def initializeGL(self):
        self._initialization_failed = False
        try:
            self._native_context = self.context()
            self._native_context.aboutToBeDestroyed.connect(self.cleanup)
            self.pm = ProjectM()
            self.pm.set_size(*self._pixel_size())
            self.pm.fps = self._fps
            if self._preset is not None:
                name, args, kwargs = self._preset
                getattr(self.pm, name)(*args, **kwargs)
            pending, self._pending = self._pending, []
            for command in pending:
                self._apply_command(command)
            self._timer.start(max(1, round(1000 / self._fps)))
            self.initialized.emit()
        except Exception as error:
            self._initialization_failed = True
            self._timer.stop()
            self.error.emit(error)

    def _pixel_size(self) -> tuple[int, int]:
        ratio = self.devicePixelRatioF()
        return max(1, round(self.width() * ratio)), max(1, round(self.height() * ratio))

    def resizeGL(self, width, height):
        if self.pm is not None:
            try:
                self.pm.set_size(*self._pixel_size())
            except Exception as error:
                self.error.emit(error)

    def paintGL(self):
        if self.pm is None and not self._initialization_failed:
            self.initializeGL()
        if self.pm is not None:
            try:
                self.pm.set_size(*self._pixel_size())
                self.pm.render(framebuffer=int(self.defaultFramebufferObject()))
                self.frame_rendered.emit()
            except Exception as error:
                self._timer.stop()
                self.error.emit(error)

    @Slot(object)
    def _apply_command(self, command):
        if self.pm is None:
            self._pending.append(command)
            return
        name, args, kwargs = command
        try:
            with self.current(), GLStateGuard():
                if name == "__fps__":
                    self.pm.fps = args[0]
                else:
                    getattr(self.pm, name)(*args, **kwargs)
                    if name in ("load_preset_file", "load_preset_data"):
                        self._preset = command
        except Exception as error:
            self.error.emit(error)
        self.update()

    def load_preset_file(self, path, *, smooth: bool = True) -> None:
        self._command.emit(("load_preset_file", (path,), {"smooth": smooth}))

    load_preset = load_preset_file

    def load_preset_data(self, data: str, *, smooth: bool = True) -> None:
        self._command.emit(("load_preset_data", (data,), {"smooth": smooth}))

    def add_pcm(self, samples, channels: int | None = None) -> None:
        self._command.emit(("add_pcm", (np.array(samples, copy=True, order="C"), channels), {}))

    @contextmanager
    def current(self):
        """Expose the core on the GUI thread with the widget's GL context current."""
        require_gui_thread()
        if self.pm is None:
            raise RuntimeError("The projectM widget has not initialized OpenGL")
        previous = QOpenGLContext.currentContext()
        surface = previous.surface() if previous is not None else None
        unchanged = previous == self.context()
        try:
            if not unchanged:
                self.makeCurrent()
            self.pm._check_alive()
            yield self.pm
        finally:
            if not unchanged:
                if previous is not None and surface is not None:
                    if not previous.makeCurrent(surface):
                        raise RuntimeError("Qt could not restore the preceding OpenGL context")
                else:
                    self.doneCurrent()

    @Slot()
    def cleanup(self) -> None:
        require_gui_thread()
        self._timer.stop()
        self._initialization_failed = False
        if self.pm is not None:
            try:
                with self.current() as pm:
                    pm.close()
                self.pm = None
            except Exception as error:
                self.error.emit(error)
        if self._native_context is not None:
            try:
                self._native_context.aboutToBeDestroyed.disconnect(self.cleanup)
            except (RuntimeError, TypeError):
                pass
            self._native_context = None

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)

    def event(self, event):
        if hasattr(self, "_timer") and event.type() in (
            QEvent.Type.DeferredDelete, QEvent.Type.ParentAboutToChange
        ):
            self.cleanup()
        return super().event(event)
