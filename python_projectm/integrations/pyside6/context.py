"""Qt OpenGL adapters with explicit surface and thread ownership."""

from contextlib import contextmanager

from PySide6.QtCore import QThread
from PySide6.QtGui import QGuiApplication, QOffscreenSurface, QOpenGLContext, QSurfaceFormat
from shiboken6 import delete

from python_projectm.utils.threading import ThreadGuard


def require_gui_thread() -> None:
    app = QGuiApplication.instance()
    if app is None or QThread.currentThread() != app.thread():
        raise RuntimeError("This operation requires a QGuiApplication and its GUI thread")


def opengl_format() -> QSurfaceFormat:
    format = QSurfaceFormat()
    format.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    return format


class QtGLContext:
    """Borrow a Qt context and surface, restoring the preceding Qt context."""

    def __init__(self, ctx: QOpenGLContext, surface=None):
        self._ctx = ctx
        self._surface = surface if surface is not None else ctx.surface()
        if self._surface is None:
            raise ValueError("Pass a surface when the Qt context has not been made current")
        self._thread = ThreadGuard()
        self._closed = False

    def _check(self):
        self._thread.check()
        if self._closed:
            raise RuntimeError("Qt context adapter is closed")

    def make_current(self) -> None:
        self._check()
        if not self._ctx.makeCurrent(self._surface):
            raise RuntimeError("Qt could not make the OpenGL context current")

    def done_current(self) -> None:
        self._check()
        self._ctx.doneCurrent()

    @contextmanager
    def current(self):
        self._check()
        previous = QOpenGLContext.currentContext()
        previous_surface = previous.surface() if previous is not None else None
        unchanged = previous == self._ctx and previous_surface == self._surface
        try:
            if not unchanged:
                self.make_current()
            yield self
        finally:
            if not unchanged:
                if previous is not None and previous_surface is not None:
                    if not previous.makeCurrent(previous_surface):
                        raise RuntimeError("Qt could not restore the preceding OpenGL context")
                else:
                    self._ctx.doneCurrent()

    def get_size(self) -> tuple[int, int]:
        self._check()
        size = self._surface.size()
        ratio = self._surface.devicePixelRatio() if hasattr(self._surface, "devicePixelRatio") else 1
        return round(size.width() * ratio), round(size.height() * ratio)


class QtOffscreenContext(QtGLContext):
    """Own an offscreen Qt context and surface on the GUI thread."""

    def __init__(self, *, share_context: QOpenGLContext | None = None):
        require_gui_thread()
        surface = QOffscreenSurface()
        surface.setFormat(share_context.format() if share_context else opengl_format())
        surface.create()
        if not surface.isValid():
            delete(surface)
            raise RuntimeError("Qt could not create an offscreen OpenGL surface")
        context = QOpenGLContext()
        context.setFormat(surface.format())
        if share_context is not None:
            context.setShareContext(share_context)
        if not context.create():
            delete(context)
            surface.destroy()
            delete(surface)
            raise RuntimeError("Qt could not create an offscreen OpenGL context")
        super().__init__(context, surface)

    def close(self) -> None:
        if self._closed:
            return
        self._check()
        require_gui_thread()
        if QOpenGLContext.currentContext() == self._ctx:
            self._ctx.doneCurrent()
        delete(self._ctx)
        self._surface.destroy()
        delete(self._surface)
        self._closed = True

    destroy = close

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
