"""Borrow an existing GLFW window or own a new desktop OpenGL window."""

import ctypes
import sys
import threading
from contextlib import contextmanager

try:
    import glfw
except ImportError as error:
    raise ImportError("GLFW integration requires the package's 'glfw' extra") from error

from python_projectm.core.validation import dimensions
from python_projectm.gl.context import current_context_id
from python_projectm.utils.threading import ThreadGuard


def _window_id(window) -> int:
    return ctypes.cast(window, ctypes.c_void_p).value or 0


def _main_thread() -> None:
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("GLFW initialization, window operations, and event polling require the main thread")


class GLFWContext:
    """Own only windows created by this adapter; never terminate global GLFW state.

    Creating a window uses and resets GLFW's global window hints. Applications
    with custom hints should create their window first and pass it to this class.
    """

    def __init__(self, window=None, *, width: int = 1280, height: int = 720,
                 title: str = "projectM", visible: bool = True, share=None):
        self._thread = ThreadGuard()
        self._closed = False
        self._owned = window is None
        if window is None:
            _main_thread()
            width, height = dimensions(width, height)
            if not glfw.init():
                raise RuntimeError("GLFW initialization failed")
            glfw.default_window_hints()
            try:
                glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
                glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
                glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
                glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
                glfw.window_hint(glfw.VISIBLE, glfw.TRUE if visible else glfw.FALSE)
                if sys.platform == "darwin":
                    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
                window = glfw.create_window(width, height, title, None, share)
            finally:
                glfw.default_window_hints()
            if not window:
                raise RuntimeError("GLFW could not create a desktop OpenGL 3.3 window")
        self.window = window

    def _check(self):
        self._thread.check()
        if self._closed:
            raise RuntimeError("GLFW context adapter is closed")

    def make_current(self) -> None:
        """Make this window's context current on the adapter's creating thread."""
        self._check()
        glfw.make_context_current(self.window)
        if _window_id(glfw.get_current_context()) != _window_id(self.window):
            raise RuntimeError("GLFW could not make the requested context current")

    def done_current(self) -> None:
        """Clear GLFW's current context; use :meth:`current` to restore one."""
        self._check()
        glfw.make_context_current(None)

    @contextmanager
    def current(self):
        """Activate this context and restore the preceding GLFW context on exit.

        Release any non-GLFW context before entering this scope. The adapter
        cannot restore a context supplied by a different toolkit.
        """
        self._check()
        previous = glfw.get_current_context()
        if not previous and current_context_id():
            raise RuntimeError(
                "A non-GLFW context is current. Release it first or pass its context adapter."
            )
        try:
            self.make_current()
            yield self
        finally:
            glfw.make_context_current(previous)

    def get_size(self) -> tuple[int, int]:
        """Return framebuffer dimensions in physical pixels on the main thread."""
        self._check()
        _main_thread()
        return tuple(glfw.get_framebuffer_size(self.window))

    def close(self) -> None:
        """Close the adapter and destroy its owned window on the main thread.

        Borrowed windows remain alive. Global GLFW state is never terminated.
        Close renderers and other GL resources before closing their context.
        """
        if self._closed:
            return
        self._check()
        if self._owned:
            _main_thread()
            if _window_id(glfw.get_current_context()) == _window_id(self.window):
                glfw.make_context_current(None)
            glfw.destroy_window(self.window)
        self._closed = True

    destroy = close
